import asyncio
import json
import logging
import os
from typing import List, Dict

# Import Azure AI Inference client and message types
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import (
    SystemMessage, 
    UserMessage, 
    AssistantMessage, 
    ToolMessage, 
    ChatCompletionsToolCall, 
    FunctionCall
)
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

# Import our MCP servers
from azure_mcp_server import AzureMCPServer
from github_mcp_server import GitHubMCPServer

# Load environment variables from .env file first
load_dotenv()

# Configure logging based on environment variable
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Set up logging configuration
if LOG_LEVEL == "NONE" or not LOG_LEVEL:
    # Disable logging completely
    logging.basicConfig(level=logging.CRITICAL + 1)  # Higher than CRITICAL to disable all
    logger = logging.getLogger(__name__)
    logger.disabled = True
else:
    # Map string levels to logging constants
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO, 
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    log_level = level_map.get(LOG_LEVEL, logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    logger = logging.getLogger(__name__)

# Get Azure OpenAI configuration from environment variables
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")  # Default to gpt-4o
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")  # Default to latest preview version

# Ensure required environment variables are present
if not AZURE_OPENAI_ENDPOINT or not AZURE_API_KEY:
    raise ValueError("Missing required environment variables: AZURE_OPENAI_ENDPOINT and AZURE_API_KEY")

def get_inference_endpoint(base_endpoint: str, model: str) -> str:
    """Convert Azure OpenAI endpoint to Azure AI Inference format"""
    # Check if this is a standard Azure OpenAI endpoint
    if "openai.azure.com" in base_endpoint:
        # Extract resource name from the endpoint
        resource_name = base_endpoint.split("//")[1].split(".")[0]
        # Return the inference endpoint format
        return f"https://{resource_name}.cognitiveservices.azure.com/openai/deployments/{model}"
    # Return as-is if already in correct format
    return base_endpoint

# Convert endpoint to inference format
INFERENCE_ENDPOINT = get_inference_endpoint(AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_MODEL)

def load_system_prompt():
    """Load system prompt from external file or use fallback"""
    # Build path to system prompt file
    prompt_file = os.path.join(os.path.dirname(__file__), "..", "prompts", "system_prompt_azure_ai_verbose.txt")
    
    # Try to read from file
    if os.path.exists(prompt_file):
        with open(prompt_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    
    # Fallback system prompt if file doesn't exist
    return """You are an Azure infrastructure expert assistant with comprehensive Azure and GitHub tools.
    
Automatically perform complete infrastructure analysis when requested:
- Get subscription details, resource groups, and all resources
- Analyze network topology including VNets, subnets, and security groups  
- Provide comprehensive findings without asking for permission to continue

Communicate naturally and explain your discoveries as you work."""

class SimpleToolManager:
    """Simple MCP server manager for Azure and GitHub tools"""
    
    def __init__(self):
        # Initialize server references
        self.azure_server = None
        self.github_server = None
        
    async def initialize(self):
        """Initialize both MCP servers"""
        print("Starting Azure Infrastructure Agent...")
        logger.info("Initializing MCP tool servers...")
        
        # Create and initialize Azure MCP server
        try:
            logger.info("Loading Azure MCP server...")
            self.azure_server = AzureMCPServer()
            await self.azure_server.initialize()
            
            # Log available Azure tools
            azure_tools = self.azure_server.list_tools() if self.azure_server else []
            logger.info(f"Azure MCP server loaded with {len(azure_tools)} tools:")
            for tool_name, tool_desc in azure_tools:
                logger.info(f"  - {tool_name}: {tool_desc}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Azure MCP server: {e}")
            self.azure_server = None
        
        # Create and initialize GitHub MCP server  
        try:
            logger.info("Loading GitHub MCP server...")
            self.github_server = GitHubMCPServer()
            await self.github_server.initialize()
            
            # Log available GitHub tools
            github_tools = self.github_server.list_tools() if self.github_server else []
            logger.info(f"GitHub MCP server loaded with {len(github_tools)} tools:")
            for tool_name, tool_desc in github_tools:
                logger.info(f"  - {tool_name}: {tool_desc}")
                
        except Exception as e:
            logger.error(f"Failed to initialize GitHub MCP server: {e}")
            self.github_server = None
        
        # Get tool counts for user feedback
        azure_tools = len(self.azure_server.list_tools()) if self.azure_server else 0
        github_tools = len(self.github_server.list_tools()) if self.github_server else 0
        
        logger.info(f"Tool initialization complete. Total: {azure_tools + github_tools} tools")
        print(f"Agent ready with {azure_tools} Azure tools and {github_tools} GitHub tools")

    def get_available_tools(self) -> List[Dict]:
        """Get all available tools from both servers"""
        available_tools = []
        
        # Add Azure tools if server is available
        if self.azure_server and self.azure_server.formatted_tools:
            available_tools.extend(self.azure_server.formatted_tools)
        
        # Add GitHub tools if server is available
        if self.github_server and self.github_server.formatted_tools:
            available_tools.extend(self.github_server.formatted_tools)
        
        return available_tools

    async def call_tool(self, tool_name: str, arguments: Dict) -> str:
        """Execute a tool call on the appropriate server"""
        try:
            # Log the tool call attempt
            logger.info(f"🔧 Calling tool: {tool_name}")
            logger.info(f"📝 Arguments: {json.dumps(arguments, indent=2)}")
            
            # Get list of Azure tool names
            azure_tool_names = [tool[0] for tool in self.azure_server.list_tools()] if self.azure_server else []
            
            # Check if this is an Azure tool
            if tool_name in azure_tool_names:
                logger.info(f"🔵 Routing to Azure MCP server...")
                result = await self.azure_server.call_tool(tool_name, arguments)
                logger.info(f"✅ Azure tool '{tool_name}' completed successfully")
                logger.info(f"📤 Result length: {len(str(result))} characters")
                return result
            
            # Otherwise try GitHub server
            elif self.github_server:
                logger.info(f"🐙 Routing to GitHub MCP server...")
                result = await self.github_server.call_tool(tool_name, arguments)
                logger.info(f"✅ GitHub tool '{tool_name}' completed successfully")
                logger.info(f"📤 Result length: {len(str(result))} characters")
                return result
            
            # Tool not found in either server
            else:
                logger.error(f"❌ Tool '{tool_name}' not found in any server")
                raise Exception(f"Tool {tool_name} not found in any server")
                
        except Exception as e:
            # Re-raise the exception to be handled by caller
            raise

    async def close(self):
        """Clean shutdown of both servers"""
        cleanup_errors = []
        
        # Close Azure server gracefully - let MCP handle its own task management
        if self.azure_server:
            try:
                # Give the server a chance to close normally, but don't force timeout
                close_task = asyncio.create_task(self.azure_server.close())
                await asyncio.wait_for(close_task, timeout=1.0)
            except asyncio.TimeoutError:
                # Don't cancel, just log the timeout
                cleanup_errors.append("Azure: Clean shutdown timeout (continuing)")
            except Exception as e:
                # Suppress cancel scope errors from MCP internals
                if "cancel scope" not in str(e).lower():
                    cleanup_errors.append(f"Azure: {type(e).__name__}")
        
        # Close GitHub server gracefully - let MCP handle its own task management  
        if self.github_server:
            try:
                # Give the server a chance to close normally, but don't force timeout
                close_task = asyncio.create_task(self.github_server.close())
                await asyncio.wait_for(close_task, timeout=1.0)
            except asyncio.TimeoutError:
                # Don't cancel, just log the timeout
                cleanup_errors.append("GitHub: Clean shutdown timeout (continuing)")
            except Exception as e:
                # Suppress cancel scope errors from MCP internals
                if "cancel scope" not in str(e).lower():
                    cleanup_errors.append(f"GitHub: {type(e).__name__}")
        
        # Report any significant cleanup issues (but don't crash)
        if cleanup_errors:
            print(f"Cleanup completed with warnings: {', '.join(cleanup_errors)}")
        else:
            print("Clean shutdown completed")

def convert_to_inference_messages(messages: List[Dict]) -> List:
    """Convert our message format to Azure AI Inference format"""
    inference_messages = []
    
    # Process each message in the conversation
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        
        # Convert based on message role
        if role == "system":
            # System message - contains instructions for the AI
            inference_messages.append(SystemMessage(content=content))
            
        elif role == "user":
            # User message - contains user input
            inference_messages.append(UserMessage(content=content))
            
        elif role == "assistant":
            # Assistant message - may include tool calls
            if "tool_calls" in msg and msg["tool_calls"]:
                # Convert tool calls to Azure format
                tool_calls = []
                for tool_call in msg["tool_calls"]:
                    tool_calls.append(
                        ChatCompletionsToolCall(
                            id=tool_call["id"],
                            function=FunctionCall(
                                name=tool_call["function"]["name"],
                                arguments=tool_call["function"]["arguments"]
                            )
                        )
                    )
                # Create assistant message with tool calls
                inference_messages.append(AssistantMessage(content=content, tool_calls=tool_calls))
            else:
                # Regular assistant message without tool calls
                inference_messages.append(AssistantMessage(content=content))
                
        elif role == "tool":
            # Tool result message - contains output from tool execution
            inference_messages.append(ToolMessage(content=content, tool_call_id=msg["tool_call_id"]))
    
    return inference_messages

async def main():
    """Main conversation loop with streaming responses"""
    print("Azure Infrastructure Agent")
    print("-" * 40)
    
    # Initialize the tool manager
    tool_manager = SimpleToolManager()
    await tool_manager.initialize()
    
    # Log available tools summary
    available_tools = tool_manager.get_available_tools()
    logger.info(f"🛠️  Agent ready with {len(available_tools)} total tools available")
    
    # Create Azure AI Inference client
    client = ChatCompletionsClient(
        endpoint=INFERENCE_ENDPOINT,
        credential=AzureKeyCredential(AZURE_API_KEY),
        api_version=AZURE_API_VERSION
    )
    
    # Start conversation with system prompt
    messages = [{"role": "system", "content": load_system_prompt()}]
    
    print("Agent ready! Type your requests below.")
    print("-" * 40)
    
    try:
        # Main conversation loop
        while True:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("Goodbye!")
                break
            
            # Skip empty input
            if not user_input:
                continue
            
            # Add user message to conversation
            messages.append({"role": "user", "content": user_input})
            
            # Log the user query
            logger.info(f"👤 User query: {user_input}")
            
            # Get available tools from both servers
            tools = tool_manager.get_available_tools()
            logger.info(f"🔍 Making AI request with {len(tools)} tools available")
            
            # Convert messages to Azure AI Inference format
            inference_messages = convert_to_inference_messages(messages)
            
            # Make streaming API call
            response = client.complete(
                messages=inference_messages,
                tools=tools,
                tool_choice="auto",  # Let AI decide when to use tools
                stream=True          # Enable streaming responses
            )
            
            # Initialize variables for streaming response
            assistant_content = ""
            tool_calls = []
            
            # Start printing assistant response
            print(f"\nAssistant: ", end="", flush=True)
            
            # Process streaming response chunks (simplified approach)
            for update in response:
                # Handle streaming content
                if update.choices and update.choices[0].delta:
                    if update.choices[0].delta.content:
                        content_piece = update.choices[0].delta.content
                        assistant_content += content_piece
                        print(content_piece, end="", flush=True)  # Print immediately
            
            # Add newline after streaming content
            print()
            
            # If we got content, just add it and continue
            if assistant_content.strip():
                messages.append({"role": "assistant", "content": assistant_content})
                continue
            
            # If no content was streamed, we likely have tool calls - make non-streaming call
            non_streaming_response = client.complete(
                messages=inference_messages,
                tools=tools,
                tool_choice="auto",
                stream=False  # Non-streaming to get complete tool calls
            )
            
            assistant_message = non_streaming_response.choices[0].message
            
            # Check if model wants to make tool calls
            if assistant_message.tool_calls:
                # Print any assistant message content
                if assistant_message.content:
                    print(f"Assistant: {assistant_message.content}")
                
                # Add assistant message with tool calls to conversation
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in assistant_message.tool_calls
                    ]
                })
                
                # Execute each tool call
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    try:
                        logger.info(f"🤖 AI requested tool: {function_name}")
                        print(f"Executing tool: {function_name}...")
                        
                        # Execute the tool
                        content = await tool_manager.call_tool(function_name, function_args)
                        
                        logger.info(f"📋 Tool result preview: {str(content)[:200]}...")
                        print(f"Tool {function_name} completed.")
                        
                        # Add tool result to conversation (following Azure SDK pattern)
                        messages.append({
                            "role": "tool",
                            "content": content,
                            "tool_call_id": tool_call.id
                        })
                        
                    except Exception as e:
                        # Handle tool execution errors
                        error_content = f"Error calling {function_name}: {str(e)}"
                        print(f"TOOL ERROR: {error_content}")
                        messages.append({
                            "role": "tool",
                            "content": error_content,
                            "tool_call_id": tool_call.id
                        })
                
                # Get final response after tool execution (streaming)
                inference_messages = convert_to_inference_messages(messages)
                
                final_response = client.complete(
                    messages=inference_messages,
                    tools=tools,
                    stream=True  # Stream the final response
                )
                
                # Process final streaming response
                final_content = ""
                print(f"\nAssistant: ", end="", flush=True)
                
                for update in final_response:
                    if update.choices and update.choices[0].delta:
                        if update.choices[0].delta.content:
                            content_piece = update.choices[0].delta.content
                            final_content += content_piece
                            print(content_piece, end="", flush=True)  # Stream final response
                
                # Add newline and save final response
                print()
                messages.append({"role": "assistant", "content": final_content})
                
            else:
                # No tool calls, just regular response
                if assistant_message.content:
                    print(f"Assistant: {assistant_message.content}")
                    messages.append({"role": "assistant", "content": assistant_message.content})
    
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\n\nShutting down gracefully...")
    except Exception as e:
        # Handle unexpected errors
        print(f"\nERROR: An unexpected error occurred: {str(e)}")
    
    finally:
        # Always clean up resources - suppress any asyncio context errors
        try:
            await tool_manager.close()
            print("Shutdown complete")
        except Exception as cleanup_error:
            # Suppress MCP internal task/context errors but show real issues
            if "cancel scope" not in str(cleanup_error).lower() and "CancelledError" not in str(cleanup_error):
                print(f"Warning during cleanup: {cleanup_error}")
            print("Shutdown complete")

# Run the agent when script is executed directly
if __name__ == "__main__":
    asyncio.run(main())
