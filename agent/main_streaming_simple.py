from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage, ToolMessage
from azure.core.credentials import AzureKeyCredential
from azure_mcp_server import AzureMCPServer
from github_mcp_server import GitHubMCPServer
import json, os, logging, asyncio, sys, re
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

class StreamingToolManager:
    """Simple streaming-only tool manager for Azure AI Inference"""
    
    def __init__(self):
        self.azure_server: Optional[AzureMCPServer] = None
        self.github_server: Optional[GitHubMCPServer] = None
        self.active_categories: Set[str] = set()
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
    
    async def analyze_and_load_tools(self, user_input: str):
        """Analyze input and load needed tools"""
        input_lower = user_input.lower()
        needed_categories = set()
        
        for category, config in TOOL_CATEGORIES.items():
            for keyword in config["keywords"]:
                if keyword in input_lower:
                    needed_categories.add(category)
                    break
        
        if not needed_categories:
            needed_categories = {"azure"}  # Default to Azure
        
        for category in needed_categories:
            if category not in self.active_categories:
                await self.load_category_tools(category)
    
    async def load_category_tools(self, category: str):
        if category == "azure" and self.azure_server and not self.azure_session_active:
            try:
                await self.azure_server.initialize()
                self.azure_session_active = True
                self.active_categories.add("azure")
                tools_count = len(self.azure_server.list_tools())
                print(f"🔧 Loaded {tools_count} Azure tools")
            except Exception as e:
                print(f"❌ Failed to load Azure tools: {e}")
        
        elif category == "github" and self.github_server and not self.github_session_active:
            try:
                await self.github_server.initialize()
                self.github_session_active = True
                self.active_categories.add("github")
                tools_count = len(self.github_server.list_tools())
                print(f"🔧 Loaded {tools_count} GitHub tools")
            except Exception as e:
                print(f"❌ Failed to load GitHub tools: {e}")
    
    def get_available_tools(self) -> List[Dict]:
        tools = []
        if "azure" in self.active_categories and self.azure_server:
            tools.extend(self.azure_server.formatted_tools or [])
        if "github" in self.active_categories and self.github_server:
            tools.extend(self.github_server.formatted_tools or [])
        return tools
    
    async def call_tool(self, tool_name: str, arguments: Dict) -> str:
        if "azure" in self.active_categories and self.azure_server:
            azure_tools = [tool[0] for tool in self.azure_server.list_tools()]
            if tool_name in azure_tools:
                return await self.azure_server.call_tool(tool_name, arguments)
        
        if "github" in self.active_categories and self.github_server:
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
        
        self.azure_session_active = False
        self.github_session_active = False
        self.active_categories.clear()


async def stream_with_tools(client: ChatCompletionsClient, tool_manager: StreamingToolManager, user_input: str):
    """Handle a single user input with streaming and tool calls"""
    
    # Analyze and load needed tools
    await tool_manager.analyze_and_load_tools(user_input)
    available_tools = tool_manager.get_available_tools()
    
    if not available_tools:
        print("⚠ No tools available")
        return
    
    # Create messages
    messages = [
        SystemMessage(content="You are a helpful Azure infrastructure assistant. Use the available tools to help the user."),
        UserMessage(content=user_input)
    ]
    
    # First streaming call
    print("\nAssistant: ", end="", flush=True)
    
    response = client.complete(
        model=AZURE_OPENAI_MODEL,
        messages=messages,
        tools=available_tools,
        stream=True,
    )
    
    # Process streaming response
    content = ""
    tool_calls = []
    current_tool_call = None
    tool_call_id = None
    
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta:
            delta = chunk.choices[0].delta
            
            # Handle content
            if hasattr(delta, 'content') and delta.content:
                print(delta.content, end="", flush=True)
                content += delta.content
            
            # Handle tool calls
            if hasattr(delta, 'tool_calls') and delta.tool_calls:
                for tool_call in delta.tool_calls:
                    if current_tool_call is None:
                        current_tool_call = {"id": "", "function": {"name": "", "arguments": ""}}
                        tool_calls.append(current_tool_call)
                    
                    if hasattr(tool_call, 'id') and tool_call.id and not tool_call_id:
                        tool_call_id = tool_call.id
                        current_tool_call["id"] = tool_call_id
                    
                    if hasattr(tool_call, 'function') and tool_call.function:
                        function = tool_call.function
                        if hasattr(function, 'name') and function.name and not current_tool_call["function"]["name"]:
                            current_tool_call["function"]["name"] = function.name
                        if hasattr(function, 'arguments') and function.arguments:
                            current_tool_call["function"]["arguments"] += function.arguments
    
    # If we have tool calls, execute them and get final response
    if tool_calls and tool_calls[0]["function"]["name"]:
        print("\n🔧 Executing tool...")
        
        try:
            tool_call = tool_calls[0]
            function_name = tool_call["function"]["name"]
            function_args = json.loads(tool_call["function"]["arguments"])
            
            # Execute the tool
            tool_result = await tool_manager.call_tool(function_name, function_args)
            
            # Create new conversation with tool result for final response
            final_messages = [
                SystemMessage(content="You are a helpful Azure infrastructure assistant. Provide a clear summary of the tool results."),
                UserMessage(content=f"User asked: {user_input}"),
                AssistantMessage(content=f"I used the {function_name} tool and got this result. Let me summarize it for you."),
                ToolMessage(content=tool_result, tool_call_id=tool_call["id"])
            ]
            
            # Get final streaming response
            print("Assistant: ", end="", flush=True)
            
            final_response = client.complete(
                model=AZURE_OPENAI_MODEL,
                messages=final_messages,
                stream=True,
            )
            
            for chunk in final_response:
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        print(delta.content, end="", flush=True)
            
            print()  # New line
            
        except Exception as e:
            print(f"\n❌ Tool execution failed: {e}")
    
    elif content:
        print()  # New line if we had content but no tool calls


async def main():
    """Main conversation loop"""
    print("\n🤖 Azure AI Inference Infrastructure Agent (Streaming Only)")
    print("💡 Type 'exit' to quit\n")
    
    # Initialize
    credential = AzureKeyCredential(AZURE_API_KEY)
    client = ChatCompletionsClient(endpoint=INFERENCE_ENDPOINT, credential=credential)
    tool_manager = StreamingToolManager()
    await tool_manager.initialize_servers()
    
    try:
        while True:
            user_input = input("Prompt: ")
            if user_input.lower() == 'exit':
                break
            
            try:
                await stream_with_tools(client, tool_manager, user_input)
            except Exception as e:
                print(f"An error occurred: {e}")
    
    except KeyboardInterrupt:
        print("\nExiting...")
    
    finally:
        print("\n🧹 Cleaning up...")
        await tool_manager.cleanup()
        print("👋 Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())
