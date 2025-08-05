from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
from azure_mcp_server import AzureMCPServer
import json, os, logging, asyncio, sys
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)
load_dotenv()

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")

# Ensure the endpoint has https:// protocol
if AZURE_OPENAI_ENDPOINT and not AZURE_OPENAI_ENDPOINT.startswith(('http://', 'https://')):
    AZURE_OPENAI_ENDPOINT = f"https://{AZURE_OPENAI_ENDPOINT}"

# Validate configuration
if not AZURE_OPENAI_ENDPOINT:
    raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is not set")

# Initialize Azure credentials
credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(
    credential, "https://cognitiveservices.azure.com/.default"
)

# Debug: Check which credential is being used
try:
    token = credential.get_token("https://cognitiveservices.azure.com/.default")
    # Suppress verbose credential checking
except Exception as e:
    logger.error(f"Authentication failed: {e}")


async def run():
    # Initialize Azure OpenAI client
    client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version="2024-04-01-preview",
        azure_ad_token_provider=token_provider,
    )

    # Initialize Azure MCP Server
    mcp_server = AzureMCPServer()
    
    async with mcp_server.create_session():
        # Display available tools
        tools = mcp_server.list_tools()
        print(f"Loaded {len(tools)} Azure MCP tools:")
        for tool_name, tool_desc in tools:
            # Show just the first sentence of the description
            short_desc = tool_desc.split('.')[0] if '.' in tool_desc else tool_desc[:60]
            print(f"  • {tool_name}: {short_desc}")

        # Get formatted tools for OpenAI
        available_tools = mcp_server.formatted_tools

        # Start conversational loop
        messages = []
        print("\nReady for conversation. Type 'exit' to quit.")
        
        while True:
            try:
                user_input = input("\nPrompt: ")
                if user_input.lower() == 'exit':
                    break
                    
                messages.append({"role": "user", "content": user_input})

                # First API call with tool configuration
                response = client.chat.completions.create(
                    model=AZURE_OPENAI_MODEL,
                    messages=messages,
                    tools=available_tools,
                    stream=True,
                )

                # Process the streaming response
                response_message = {"role": "assistant", "content": "", "tool_calls": []}
                current_tool_call = None
                
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta:
                        delta = chunk.choices[0].delta
                        
                        # Handle content streaming
                        if delta.content:
                            if not response_message["content"]:
                                print("\nAssistant: ", end="", flush=True)
                            print(delta.content, end="", flush=True)
                            response_message["content"] += delta.content
                        
                        # Handle tool call streaming
                        if delta.tool_calls:
                            for tool_call in delta.tool_calls:
                                if tool_call.index is not None:
                                    # Ensure we have enough tool calls in our list
                                    while len(response_message["tool_calls"]) <= tool_call.index:
                                        response_message["tool_calls"].append({
                                            "id": "",
                                            "type": "function",
                                            "function": {"name": "", "arguments": ""}
                                        })
                                    
                                    current_tool_call = response_message["tool_calls"][tool_call.index]
                                    
                                    if tool_call.id:
                                        current_tool_call["id"] = tool_call.id
                                    if tool_call.function:
                                        if tool_call.function.name:
                                            current_tool_call["function"]["name"] = tool_call.function.name
                                        if tool_call.function.arguments:
                                            current_tool_call["function"]["arguments"] += tool_call.function.arguments

                # Clean up empty content if we only had tool calls
                if not response_message["content"] and response_message["tool_calls"]:
                    response_message["content"] = None
                
                # Clean up empty tool calls
                if not any(tc["function"]["name"] for tc in response_message["tool_calls"]):
                    response_message["tool_calls"] = None
                
                # Convert to the format expected by the messages list
                if response_message["tool_calls"]:
                    # Convert our format to OpenAI's expected format
                    formatted_tool_calls = []
                    for tc in response_message["tool_calls"]:
                        if tc["function"]["name"]:  # Only include valid tool calls
                            formatted_tool_calls.append({
                                "id": tc["id"],
                                "type": "function", 
                                "function": {
                                    "name": tc["function"]["name"],
                                    "arguments": tc["function"]["arguments"]
                                }
                            })
                    
                    response_dict = {
                        "role": "assistant",
                        "content": response_message["content"],
                        "tool_calls": formatted_tool_calls if formatted_tool_calls else None
                    }
                else:
                    response_dict = {
                        "role": "assistant", 
                        "content": response_message["content"]
                    }
                    
                messages.append(response_dict)

                # Handle function calls
                if response_dict.get("tool_calls"):
                    for tool_call in response_dict["tool_calls"]:
                        try:
                            function_name = tool_call["function"]["name"]
                            function_args = json.loads(tool_call["function"]["arguments"])
                            
                            # Call the tool using Azure MCP Server
                            content = await mcp_server.call_tool(function_name, function_args)
                            
                            # Add the tool response to messages
                            messages.append(
                                {
                                    "tool_call_id": tool_call["id"],
                                    "role": "tool",
                                    "name": function_name,
                                    "content": content,
                                }
                            )
                        except Exception as e:
                            logger.error(f"Error calling tool {function_name}: {e}")
                            messages.append(
                                {
                                    "tool_call_id": tool_call["id"],
                                    "role": "tool",
                                    "name": function_name,
                                    "content": f"Error calling tool: {str(e)}",
                                }
                            )

                    # Get the final response from the model after tool calls
                    final_response = client.chat.completions.create(
                        model=AZURE_OPENAI_MODEL,
                        messages=messages,
                        tools=available_tools,
                        stream=True,
                    )

                    # Stream the final response
                    print("\nAssistant: ", end="", flush=True)
                    for chunk in final_response:
                        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                            print(chunk.choices[0].delta.content, end="", flush=True)
                    print()  # New line after streaming
                elif response_dict.get("content"):
                    print()  # New line after streaming if we had content but no tool calls
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                
                # Try to recover by resetting the conversation if it's a connection error
                if "connection" in str(e).lower():
                    print("Connection error detected. You may need to restart the script.")
                    break


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)