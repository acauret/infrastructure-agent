import asyncio
import json
import logging
import os
import re
import sys
from typing import List, Dict, Set, Optional

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

from azure_mcp_server import AzureMCPServer
from github_mcp_server import GitHubMCPServer

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

def get_inference_endpoint(base_endpoint: str, model: str) -> str:
    """Convert endpoint format for Azure AI Inference"""
    if "openai.azure.com" in base_endpoint:
        resource_name = base_endpoint.split("//")[1].split(".")[0]
        return f"https://{resource_name}.cognitiveservices.azure.com/openai/deployments/{model}"
    return base_endpoint

INFERENCE_ENDPOINT = get_inference_endpoint(AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_MODEL)

# Load the verbose system prompt
def load_system_prompt():
    """Load system prompt from file"""
    prompt_file = os.path.join(os.path.dirname(__file__), "..", "prompts", "system_prompt_azure_ai_verbose.txt")
    if os.path.exists(prompt_file):
        with open(prompt_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    
    # Fallback verbose prompt if file doesn't exist
    return """You are an Azure infrastructure expert assistant with comprehensive GitHub and Azure tools.

## AUTONOMOUS EXECUTION - COMPLETE ALL TASKS
**CRITICAL**: When a user asks for infrastructure analysis, automatically perform ALL related discovery steps:
- If asked about subscriptions → automatically get subscription details AND resource groups AND resources
- If asked about networks → automatically get VNets AND subnets AND NSGs AND routing
- If asked about resources → automatically enumerate ALL resource types across ALL resource groups
- Continue until you have provided a COMPLETE analysis

## COMMUNICATION STYLE
Communicate naturally like an Azure expert. Explain what you're discovering and continue seamlessly to provide comprehensive analysis without asking permission.

Always complete the full scope of infrastructure discovery automatically."""

# Tool categorization for dynamic loading
TOOL_CATEGORIES = {
    "azure": {
        "keywords": [
            "azure", "subscription", "resource group", "aks", "kubernetes", 
            "vm", "virtual machine", "storage", "blob", "container", "database",
            "sql", "cosmos", "policy", "rbac", "management group", "tenant",
            "activity log", "monitor", "network", "vnet", "subnet", "firewall"
        ],
        "default_on": True
    },
    "github": {
        "keywords": [
            "github", "repository", "repo", "commit", "pull request", "pr",
            "branch", "file", "directory", "code", "readme", "markdown",
            "issue", "workflow", "action", "clone", "fork", "organization"
        ],
        "default_on": True
    }
}

class VerboseDynamicToolManager:
    """Enhanced tool manager with detailed step-by-step feedback"""
    
    def __init__(self):
        self.azure_server = None
        self.github_server = None
        self.active_categories: Set[str] = set()
        self.azure_tools = []
        self.github_tools = []
        
    async def initialize(self):
        """Initialize MCP servers"""
        print("Starting Azure Infrastructure Agent...")
        
        self.azure_server = AzureMCPServer()
        await self.azure_server.initialize()
        
        self.github_server = GitHubMCPServer()
        await self.github_server.initialize()
        
        await self.load_all_tools()
        print(f"Agent ready with {len(self.azure_tools)} Azure tools and {len(self.github_tools)} GitHub tools")

    async def load_all_tools(self):
        """Load tools from both servers"""
        self.azure_tools = self.azure_server.list_tools()
        self.github_tools = self.github_server.list_tools()
        
        # Activate both categories by default
        self.active_categories.add("azure")
        self.active_categories.add("github")

    def detect_needed_categories(self, text: str) -> Set[str]:
        """Analyze text and determine which tool categories are needed"""
        text_lower = text.lower()
        needed = set()
        
        for category, config in TOOL_CATEGORIES.items():
            for keyword in config["keywords"]:
                if keyword in text_lower:
                    needed.add(category)
                    break
        
        if not needed:
            needed = {"azure", "github"}  # Default to both
            
        return needed

    async def ensure_categories_loaded(self, categories: Set[str]):
        """Ensure specified tool categories are loaded"""
        for category in categories:
            if category not in self.active_categories:
                print(f"🔧 **LOADING CATEGORY**: {category}")
                self.active_categories.add(category)
                print(f"✅ **ACTIVATED**: {category} tools now available")

    def get_available_tools(self) -> List[Dict]:
        """Get formatted tools for the current categories"""
        available_tools = []
        
        if "azure" in self.active_categories and self.azure_server:
            available_tools.extend(self.azure_server.formatted_tools or [])
        
        if "github" in self.active_categories and self.github_server:
            available_tools.extend(self.github_server.formatted_tools or [])
        
        return available_tools

    async def call_tool_with_feedback(self, tool_name: str, arguments: Dict) -> str:
        """Execute tool call silently and return results for natural presentation"""
        
        try:
            # Call the appropriate tool method
            if "azure" in self.active_categories and tool_name in [tool[0] for tool in self.azure_tools]:
                result = await self.azure_server.call_tool(tool_name, arguments)
            elif "github" in self.active_categories and tool_name in [tool[0] for tool in self.github_tools]:
                result = await self.github_server.call_tool(tool_name, arguments)
            else:
                raise Exception(f"Tool {tool_name} not found in active categories: {self.active_categories}")
            
            return result
            
        except Exception as e:
            raise

    def _explain_tool_purpose(self, tool_name: str, args: Dict) -> str:
        """Explain why we're using this specific tool"""
        explanations = {
            "get_file_contents": f"Reading {args.get('path', 'file')} to understand its structure and content",
            "get_repository": f"Getting repository information for {args.get('repo', 'unknown')} to understand setup",
            "list_directory": f"Exploring {args.get('path', 'directory')} to see file organization",
            "create_branch": f"Creating branch '{args.get('branch', 'new-branch')}' to isolate our changes",
            "create_or_update_file": f"Creating/updating {args.get('path', 'file')} with new content",
            "create_pull_request": f"Opening PR to merge changes from {args.get('head', 'branch')} to {args.get('base', 'main')}",
            "search_code": f"Searching for '{args.get('q', 'code')}' to find existing implementations",
            "get_subscriptions": "Retrieving list of Azure subscriptions to understand available resources",
            "get_resource_groups": f"Getting resource groups in subscription {args.get('subscription_id', 'current')} to see organization",
            "get_resources": f"Listing resources in {args.get('resource_group_name', 'resource group')} to inventory components",
        }
        return explanations.get(tool_name, f"Using {tool_name} to accomplish the current step")

    def _analyze_result(self, tool_name: str, result: str) -> str:
        """Provide intelligent analysis of tool results"""
        if tool_name == "get_file_contents":
            if "policy" in result.lower():
                return "Found policy-related content - will analyze structure and patterns"
            elif ".json" in result:
                return "Found JSON content - will examine for policy definitions"
            elif "readme" in tool_name.lower():
                return "Found documentation - will review for contribution guidelines"
            else:
                return "Retrieved file content - will analyze for relevant information"
        elif tool_name == "get_repository":
            return "Got repository metadata - will use this to understand project structure"
        elif tool_name == "list_directory":
            file_count = result.count("\n") if result else 0
            return f"Found {file_count} items - will examine for relevant files and patterns"
        elif tool_name == "get_subscriptions":
            subscription_count = result.count("subscription_id") if result else 0
            return f"Found {subscription_count} subscriptions - will select appropriate one for operations"
        elif tool_name == "get_resource_groups":
            rg_count = result.count("resourceGroup") if result else 0
            return f"Found {rg_count} resource groups - will analyze for target deployment location"
        elif tool_name == "create_branch":
            return "Branch created successfully - ready to make changes in isolation"
        elif tool_name == "create_or_update_file":
            return "File operation completed - changes are now ready for review"
        elif tool_name == "create_pull_request":
            return "Pull request created - ready for review and collaboration"
        else:
            return "Operation completed successfully - proceeding with next step"

    async def close(self):
        """Clean shutdown"""
        cleanup_errors = []
        
        # Close Azure server
        if self.azure_server:
            try:
                await asyncio.wait_for(self.azure_server.close(), timeout=1.0)
            except (asyncio.TimeoutError, asyncio.CancelledError, RuntimeError) as e:
                cleanup_errors.append(f"Azure {type(e).__name__}")
            except Exception as e:
                cleanup_errors.append(f"Azure: {e}")
        
        # Close GitHub server  
        if self.github_server:
            try:
                await asyncio.wait_for(self.github_server.close(), timeout=1.0)
            except (asyncio.TimeoutError, asyncio.CancelledError, RuntimeError) as e:
                cleanup_errors.append(f"GitHub {type(e).__name__}")
            except Exception as e:
                cleanup_errors.append(f"GitHub: {e}")
        
        if cleanup_errors:
            print(f"Cleanup completed with warnings: {', '.join(cleanup_errors)}")
        else:
            print("Clean shutdown completed")

def convert_to_inference_messages(messages: List[Dict]) -> List:
    """Convert conversation messages to Azure AI Inference format"""
    inference_messages = []
    
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        
        if role == "system":
            inference_messages.append(SystemMessage(content=content))
        elif role == "user":
            inference_messages.append(UserMessage(content=content))
        elif role == "assistant":
            if "tool_calls" in msg and msg["tool_calls"]:
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
                inference_messages.append(
                    AssistantMessage(content=content, tool_calls=tool_calls)
                )
            else:
                inference_messages.append(AssistantMessage(content=content))
        elif role == "tool":
            inference_messages.append(
                ToolMessage(content=content, tool_call_id=msg["tool_call_id"])
            )
    
    return inference_messages

async def main():
    """Main conversation loop with autonomous execution"""
    print("Azure Infrastructure Agent")
    print("-" * 40)
    
    # Initialize the tool manager
    tool_manager = VerboseDynamicToolManager()
    await tool_manager.initialize()
    
    # Initialize the client
    client = ChatCompletionsClient(
        endpoint=INFERENCE_ENDPOINT,
        credential=AzureKeyCredential(AZURE_API_KEY)
    )
    
    # Start conversation
    messages = [{"role": "system", "content": load_system_prompt()}]
    
    print("Agent ready! Type your requests below.")
    print("-" * 40)
    
    try:
        while True:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Detect and ensure needed tool categories (silent)
            needed_categories = tool_manager.detect_needed_categories(user_input)
            await tool_manager.ensure_categories_loaded(needed_categories)
            
            # Add user message
            messages.append({"role": "user", "content": user_input})
            
            # Get available tools
            tools = tool_manager.get_available_tools()
            
            # Make API call with streaming
            inference_messages = convert_to_inference_messages(messages)
            
            response = client.complete(
                messages=inference_messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=2000,
                stream=True
            )
            
            # Handle streaming response
            assistant_content = ""
            tool_calls = []
            
            print(f"\nAssistant: ", end="", flush=True)
            
            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    choice = chunk.choices[0]
                    
                    # Handle content streaming
                    if choice.delta.content:
                        content_piece = choice.delta.content
                        assistant_content += content_piece
                        print(content_piece, end="", flush=True)
                    
                    # Handle tool calls
                    if choice.delta.tool_calls:
                        for tool_call_delta in choice.delta.tool_calls:
                            # Extend tool_calls list if needed
                            while len(tool_calls) <= tool_call_delta.index:
                                tool_calls.append({
                                    "id": "",
                                    "function": {"name": "", "arguments": ""}
                                })
                            
                            # Update the tool call at the specific index
                            if tool_call_delta.id:
                                tool_calls[tool_call_delta.index]["id"] = tool_call_delta.id
                            if tool_call_delta.function:
                                if tool_call_delta.function.name:
                                    tool_calls[tool_call_delta.index]["function"]["name"] = tool_call_delta.function.name
                                if tool_call_delta.function.arguments:
                                    tool_calls[tool_call_delta.index]["function"]["arguments"] += tool_call_delta.function.arguments
            
            print()  # New line after streaming content
            
            # Create assistant message
            assistant_message_data = {
                "role": "assistant", 
                "content": assistant_content
            }
            
            # Handle tool calls if present
            if tool_calls and any(tc["id"] for tc in tool_calls):
                # Format tool calls for message history
                formatted_tool_calls = [
                    {
                        "id": tc["id"],
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"]
                        }
                    } for tc in tool_calls if tc["id"]
                ]
                
                assistant_message_data["tool_calls"] = formatted_tool_calls
                messages.append(assistant_message_data)
                
                # Execute each tool call
                for tool_call in tool_calls:
                    if not tool_call["id"]:  # Skip incomplete tool calls
                        continue
                        
                    function_name = tool_call["function"]["name"]
                    function_args = json.loads(tool_call["function"]["arguments"])
                    
                    try:
                        # Use concise tool calling
                        content = await tool_manager.call_tool_with_feedback(function_name, function_args)
                        
                        # Add tool result
                        messages.append({
                            "role": "tool",
                            "content": content,
                            "tool_call_id": tool_call["id"]
                        })
                        
                    except Exception as e:
                        error_content = f"Error calling {function_name}: {str(e)}"
                        print(f"TOOL ERROR: {error_content}")
                        messages.append({
                            "role": "tool",
                            "content": error_content,
                            "tool_call_id": tool_call["id"]
                        })
                
                # Get final response after tool execution with streaming
                inference_messages = convert_to_inference_messages(messages)
                
                final_response = client.complete(
                    messages=inference_messages,
                    temperature=0.7,
                    max_tokens=2000,
                    stream=True
                )
                
                final_content = ""
                print(f"\nAssistant: ", end="", flush=True)
                
                for chunk in final_response:
                    if chunk.choices and len(chunk.choices) > 0:
                        choice = chunk.choices[0]
                        if choice.delta.content:
                            content_piece = choice.delta.content
                            final_content += content_piece
                            print(content_piece, end="", flush=True)
                
                print()  # New line after streaming
                messages.append({"role": "assistant", "content": final_content})
                
            else:
                # No tool calls, just regular response
                messages.append(assistant_message_data)
    
    except KeyboardInterrupt:
        print("\n\n🛑 **INTERRUPTED**: Shutting down gracefully...")
    except Exception as e:
        print(f"\n❌ **ERROR**: An unexpected error occurred: {str(e)}")
    
    finally:
        await tool_manager.close()
        print("✅ **SHUTDOWN COMPLETE**: All resources cleaned up")

if __name__ == "__main__":
    asyncio.run(main())
