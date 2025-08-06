from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from azure_mcp_server import AzureMCPServer
from github_mcp_server import GitHubMCPServer
import json, os, logging, asyncio, sys
from dotenv import load_dotenv
from typing import List, Dict, Set, Optional

# Setup logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
load_dotenv()

# Azure AI Inference configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")

if not AZURE_OPENAI_ENDPOINT or not AZURE_API_KEY:
    raise ValueError("Missing required environment variables: AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY")

# Convert endpoint format
def get_inference_endpoint(base_endpoint: str, model: str) -> str:
    if "openai.azure.com" in base_endpoint:
        resource_name = base_endpoint.split("//")[1].split(".")[0]
        return f"https://{resource_name}.cognitiveservices.azure.com/openai/deployments/{model}"
    return base_endpoint

INFERENCE_ENDPOINT = get_inference_endpoint(AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_MODEL)

# Tool categories for dynamic loading
TOOL_CATEGORIES = {
    "azure": {
        "keywords": ["azure", "subscription", "resource", "aks", "sql", "storage", "cosmos", "keyvault"],
    },
    "github": {
        "keywords": ["github", "repository", "repo", "pull request", "pr", "issue", "commit"],
    }
}

class SimpleToolManager:
    """Simplified tool manager for Azure AI Inference streaming"""
    
    def __init__(self):
        self.azure_server: Optional[AzureMCPServer] = None
        self.github_server: Optional[GitHubMCPServer] = None
        self.azure_session_active = False
        self.github_session_active = False
    
    async def initialize_servers(self):
        try:
            self.azure_server = AzureMCPServer()
            print("✓ Azure MCP Server initialized")
        except Exception as e:
            print(f"⚠ Azure MCP Server failed: {e}")
        
        try:
            self.github_server = GitHubMCPServer()
            print("✓ GitHub MCP Server initialized")
        except Exception as e:
            print(f"⚠ GitHub MCP Server failed: {e}")
    
    async def load_tools_for_input(self, user_input: str):
        """Load tools based on user input"""
        input_lower = user_input.lower()
        
        # Check for Azure keywords
        azure_keywords = TOOL_CATEGORIES["azure"]["keywords"]
        if any(keyword in input_lower for keyword in azure_keywords):
            await self.ensure_azure_loaded()
        
        # Check for GitHub keywords  
        github_keywords = TOOL_CATEGORIES["github"]["keywords"]
        if any(keyword in input_lower for keyword in github_keywords):
            await self.ensure_github_loaded()
        
        # Default to Azure if nothing detected
        if not self.azure_session_active and not self.github_session_active:
            await self.ensure_azure_loaded()
    
    async def ensure_azure_loaded(self):
        if not self.azure_session_active and self.azure_server:
            try:
                await self.azure_server.initialize()
                self.azure_session_active = True
                tools_count = len(self.azure_server.list_tools())
                print(f"🔧 Loaded {tools_count} Azure tools")
            except Exception as e:
                print(f"❌ Failed to load Azure tools: {e}")
    
    async def ensure_github_loaded(self):
        if not self.github_session_active and self.github_server:
            try:
                await self.github_server.initialize()
                self.github_session_active = True
                tools_count = len(self.github_server.list_tools())
                print(f"🔧 Loaded {tools_count} GitHub tools")
            except Exception as e:
                print(f"❌ Failed to load GitHub tools: {e}")
    
    def get_available_tools(self) -> List[Dict]:
        tools = []
        if self.azure_session_active and self.azure_server:
            tools.extend(self.azure_server.formatted_tools or [])
        if self.github_session_active and self.github_server:
            tools.extend(self.github_server.formatted_tools or [])
        return tools
    
    async def execute_tool(self, tool_name: str, arguments: Dict) -> str:
        # Try Azure first
        if self.azure_session_active and self.azure_server:
            azure_tools = [tool[0] for tool in self.azure_server.list_tools()]
            if tool_name in azure_tools:
                return await self.azure_server.call_tool(tool_name, arguments)
        
        # Try GitHub
        if self.github_session_active and self.github_server:
            github_tools = [tool[0] for tool in self.github_server.list_tools()]
            if tool_name in github_tools:
                return await self.github_server.call_tool(tool_name, arguments)
        
        raise Exception(f"Tool {tool_name} not found")
    
    async def cleanup(self):
        if self.azure_session_active and self.azure_server:
            try:
                await asyncio.wait_for(self.azure_server.close(), timeout=1.0)
            except:
                pass
        
        if self.github_session_active and self.github_server:
            try:
                await asyncio.wait_for(self.github_server.close(), timeout=1.0)
            except:
                pass


async def handle_user_request(client: ChatCompletionsClient, tool_manager: SimpleToolManager, user_input: str):
    """Handle a single user request with streaming response"""
    
    # Load appropriate tools
    await tool_manager.load_tools_for_input(user_input)
    available_tools = tool_manager.get_available_tools()
    
    if not available_tools:
        print("⚠ No tools available")
        return
    
    # Create messages for Azure AI Inference
    messages = [
        SystemMessage(content="""You are a helpful Azure infrastructure assistant. When users ask about Azure subscriptions, use the 'subscription' tool with the command parameter set to 'subscription_list' to get actual subscription data.

For subscription-related queries, always call: subscription tool with {"command": "subscription_list"}

Use the available tools to help the user and provide specific, actionable information."""),
        UserMessage(content=user_input)
    ]
    
    # Make streaming call
    print("\nAssistant: ", end="", flush=True)
    
    try:
        response = client.complete(
            model=AZURE_OPENAI_MODEL,
            messages=messages,
            tools=available_tools,
            stream=True,
        )
        
        # Process streaming response
        content_parts = []
        tool_calls = []
        current_tool_call = None
        
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta:
                delta = chunk.choices[0].delta
                
                # Handle content streaming
                if hasattr(delta, 'content') and delta.content:
                    print(delta.content, end="", flush=True)
                    content_parts.append(delta.content)
                
                # Handle tool call streaming
                if hasattr(delta, 'tool_calls') and delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        # Initialize tool call if needed
                        if current_tool_call is None:
                            current_tool_call = {
                                "id": "",
                                "name": "",
                                "arguments": ""
                            }
                            tool_calls.append(current_tool_call)
                        
                        # Extract tool call info
                        if hasattr(tool_call, 'id') and tool_call.id:
                            current_tool_call["id"] = tool_call.id
                        
                        if hasattr(tool_call, 'function') and tool_call.function:
                            func = tool_call.function
                            if hasattr(func, 'name') and func.name:
                                current_tool_call["name"] = func.name
                            if hasattr(func, 'arguments') and func.arguments:
                                current_tool_call["arguments"] += func.arguments
        
        # If we have a valid tool call, execute it
        if tool_calls and tool_calls[0].get("name") and tool_calls[0].get("arguments"):
            print(f"\n🔧 Executing tool: {tool_calls[0]['name']}...", flush=True)
            print(f"📋 Arguments: {tool_calls[0]['arguments']}", flush=True)
            
            try:
                tool_call = tool_calls[0]
                function_name = tool_call["name"]
                function_args = json.loads(tool_call["arguments"])
                
                print(f"🔄 Calling {function_name} with args: {function_args}")
                
                # Execute the tool
                tool_result = await tool_manager.execute_tool(function_name, function_args)
                
                print(f"✅ Tool result length: {len(tool_result)} characters")
                print(f"📊 Tool result preview: {tool_result[:200]}...")
                
                # Create a simple follow-up request for summary
                summary_messages = [
                    SystemMessage(content="You are a helpful assistant. Present the following tool result clearly and concisely to the user."),
                    UserMessage(content=f"User asked: {user_input}\n\nTool result from {function_name}:\n{tool_result}\n\nPlease present this information clearly to the user.")
                ]
                
                # Stream the summary
                print("Assistant: ", end="", flush=True)
                
                summary_response = client.complete(
                    model=AZURE_OPENAI_MODEL,
                    messages=summary_messages,
                    stream=True,
                )
                
                for chunk in summary_response:
                    if chunk.choices and chunk.choices[0].delta:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, 'content') and delta.content:
                            print(delta.content, end="", flush=True)
                
                print()  # New line
                
            except json.JSONDecodeError as e:
                print(f"\n❌ Invalid tool arguments: {e}")
            except Exception as e:
                print(f"\n❌ Tool execution failed: {e}")
        
        elif content_parts:
            print()  # New line if we had content but no tool calls
        else:
            print("(No response)")
    
    except Exception as e:
        print(f"\n❌ Request failed: {e}")


async def main():
    """Main conversation loop"""
    print("\n🤖 Azure AI Inference Infrastructure Agent")
    print("🚀 Streaming-only with dynamic tool loading")
    print("💡 Type 'exit' to quit\n")
    
    # Initialize
    credential = AzureKeyCredential(AZURE_API_KEY)
    client = ChatCompletionsClient(endpoint=INFERENCE_ENDPOINT, credential=credential)
    tool_manager = SimpleToolManager()
    await tool_manager.initialize_servers()
    
    try:
        while True:
            user_input = input("Prompt: ")
            if user_input.lower() == 'exit':
                break
            
            try:
                await handle_user_request(client, tool_manager, user_input)
            except Exception as e:
                print(f"❌ Error: {e}")
    
    except KeyboardInterrupt:
        print("\nExiting...")
    
    finally:
        print("\n🧹 Cleaning up...")
        await tool_manager.cleanup()
        print("👋 Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())
