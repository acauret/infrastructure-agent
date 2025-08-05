from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
from azure_mcp_server import AzureMCPServer
import json, os, logging, asyncio, sys
from dotenv import load_dotenv

# Setup logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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

logger.info(f"Using Azure OpenAI endpoint: {AZURE_OPENAI_ENDPOINT}")

# Initialize Azure credentials
credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(
    credential, "https://cognitiveservices.azure.com/.default"
)

# Debug: Check which credential is being used
try:
    token = credential.get_token("https://cognitiveservices.azure.com/.default")
    logger.info(f"Successfully authenticated. Token expires at: {token.expires_on}")
    
    # Try to identify the credential type
    from azure.identity import EnvironmentCredential, AzureCliCredential, ManagedIdentityCredential
    for cred_type, cred_name in [
        (EnvironmentCredential, "Environment (Service Principal)"),
        (AzureCliCredential, "Azure CLI"),
        (ManagedIdentityCredential, "Managed Identity")
    ]:
        try:
            test_cred = cred_type()
            test_token = test_cred.get_token("https://cognitiveservices.azure.com/.default")
            logger.info(f"Using credential type: {cred_name}")
            break
        except:
            continue
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
        print("\nAvailable Azure MCP tools:")
        for tool_name, tool_desc in mcp_server.list_tools():
            print(f"  - {tool_name}: {tool_desc}")

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
                logger.info("Sending request to Azure OpenAI...")
                response = client.chat.completions.create(
                    model=AZURE_OPENAI_MODEL,
                    messages=messages,
                    tools=available_tools,
                )

                # Process the model's response
                response_message = response.choices[0].message
                messages.append(response_message)

                # Handle function calls
                if response_message.tool_calls:
                    logger.info(f"Model requested {len(response_message.tool_calls)} tool call(s)")
                    
                    for tool_call in response_message.tool_calls:
                        try:
                            function_name = tool_call.function.name
                            function_args = json.loads(tool_call.function.arguments)
                            
                            # Call the tool using Azure MCP Server
                            content = await mcp_server.call_tool(function_name, function_args)
                            
                            logger.info(f"Tool {function_name} returned: {content[:200]}...")
                            
                            # Add the tool response to messages
                            messages.append(
                                {
                                    "tool_call_id": tool_call.id,
                                    "role": "tool",
                                    "name": function_name,
                                    "content": content,
                                }
                            )
                        except Exception as e:
                            logger.error(f"Error calling tool {tool_call.function.name}: {e}", exc_info=True)
                            messages.append(
                                {
                                    "tool_call_id": tool_call.id,
                                    "role": "tool",
                                    "name": tool_call.function.name,
                                    "content": f"Error calling tool: {str(e)}",
                                }
                            )
                else:
                    logger.info("No tool calls were made by the model")

                # Get the final response from the model
                logger.info("Getting final response from Azure OpenAI...")
                final_response = client.chat.completions.create(
                    model=AZURE_OPENAI_MODEL,
                    messages=messages,
                    tools=available_tools,
                )

                # Print the response
                response_content = final_response.choices[0].message.content
                if response_content:
                    print("\nAssistant:", response_content)
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                logger.error(f"Error in conversation loop: {e}", exc_info=True)
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
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)