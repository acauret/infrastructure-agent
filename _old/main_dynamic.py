from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
from azure_mcp_server import AzureMCPServer
from github_mcp_server import GitHubMCPServer
import json, os, logging, asyncio, sys, re
from dotenv import load_dotenv
from typing import List, Dict, Set, Optional

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

# Tool categorization for dynamic loading
TOOL_CATEGORIES = {
    "azure": {
        "keywords": [
            "azure", "subscription", "resource group", "aks", "kubernetes", 
            "sql", "storage", "cosmos", "keyvault", "monitor", "bicep",
            "terraform", "virtual desktop", "redis", "postgres", "service bus",
            "load testing", "grafana", "datadog", "marketplace"
        ],
        "tools": [
            "documentation", "bestpractices", "group", "subscription", "aks", 
            "appconfig", "role", "datadog", "cosmos", "foundry", "grafana",
            "keyvault", "kusto", "marketplace", "monitor", "postgres", "redis",
            "search", "servicebus", "sql", "storage", "workbooks", "bicepschema",
            "virtualdesktop", "azureterraformbestpractices", "loadtesting",
            "extension_az", "extension_azd", "extension_azqr"
        ]
    },
    "github": {
        "keywords": [
            "github", "repository", "repo", "pull request", "pr", "issue", 
            "commit", "workflow", "actions", "gist", "branch", "fork",
            "code", "search code", "organization", "user", "notification"
        ],
        "tools": [
            "add_comment_to_pending_review", "add_issue_comment", "add_sub_issue",
            "assign_copilot_to_issue", "cancel_workflow_run", "create_and_submit_pull_request_review",
            "create_branch", "create_gist", "create_issue", "create_or_update_file",
            "create_pending_pull_request_review", "create_pull_request", "create_repository",
            "delete_file", "delete_pending_pull_request_review", "delete_workflow_run_logs",
            "dismiss_notification", "download_workflow_run_artifact", "fork_repository",
            "get_code_scanning_alert", "get_commit", "get_dependabot_alert", "get_discussion",
            "get_discussion_comments", "get_file_contents", "get_issue", "get_issue_comments",
            "get_job_logs", "get_me", "get_notification_details", "get_pull_request",
            "get_pull_request_comments", "get_pull_request_diff", "get_pull_request_files",
            "get_pull_request_reviews", "get_pull_request_status", "get_secret_scanning_alert",
            "get_tag", "get_workflow_run", "get_workflow_run_logs", "get_workflow_run_usage",
            "list_branches", "list_code_scanning_alerts", "list_commits", "list_dependabot_alerts",
            "list_discussion_categories", "list_discussions", "list_gists", "list_issues",
            "list_notifications", "list_pull_requests", "list_secret_scanning_alerts",
            "list_sub_issues", "list_tags", "list_workflow_jobs", "list_workflow_run_artifacts",
            "list_workflow_runs", "list_workflows", "manage_notification_subscription",
            "manage_repository_notification_subscription", "mark_all_notifications_read",
            "merge_pull_request", "push_files", "remove_sub_issue", "reprioritize_sub_issue",
            "request_copilot_review", "rerun_failed_jobs", "rerun_workflow_run", "run_workflow",
            "search_code", "search_issues", "search_orgs", "search_pull_requests",
            "search_repositories", "search_users", "submit_pending_pull_request_review",
            "update_gist", "update_issue", "update_pull_request", "update_pull_request_branch"
        ]
    }
}

# Always-available basic tools
BASIC_TOOLS = {
    "azure": ["documentation", "bestpractices", "subscription"],
    "github": ["get_me", "search_repositories"]
}


class DynamicToolManager:
    """Manages dynamic loading and unloading of MCP tool sets"""
    
    def __init__(self):
        self.azure_server: Optional[AzureMCPServer] = None
        self.github_server: Optional[GitHubMCPServer] = None
        self.active_categories: Set[str] = set()
        self.azure_session_active = False
        self.github_session_active = False
        self.azure_tools = []
        self.github_tools = []
    
    async def analyze_conversation_context(self, messages: List[Dict], current_input: str = "") -> Set[str]:
        """Analyze conversation to determine needed tool categories"""
        # Combine all conversation text
        conversation_text = " ".join([
            msg.get("content", "") for msg in messages if msg.get("content")
        ]) + " " + current_input
        
        conversation_lower = conversation_text.lower()
        needed_categories = set()
        
        # Check for category keywords
        for category, config in TOOL_CATEGORIES.items():
            if any(keyword in conversation_lower for keyword in config["keywords"]):
                needed_categories.add(category)
        
        # Default to basic tools if nothing specific detected
        if not needed_categories and not messages:
            needed_categories = {"azure", "github"}  # Start with both basic tool sets
        
        return needed_categories
    
    async def initialize_servers(self):
        """Initialize MCP servers (but don't create sessions yet)"""
        try:
            self.azure_server = AzureMCPServer()
            print("✓ Azure MCP Server initialized")
        except Exception as e:
            print(f"⚠ Azure MCP Server initialization failed: {e}")
        
        try:
            self.github_server = GitHubMCPServer()
            print("✓ GitHub MCP Server initialized")
        except Exception as e:
            print(f"⚠ GitHub MCP Server initialization failed: {e}")
    
    async def load_category_tools(self, category: str):
        """Load tools for a specific category"""
        if category in self.active_categories:
            return  # Already loaded
        
        if category == "azure" and self.azure_server and not self.azure_session_active:
            try:
                await self.azure_server.initialize()
                self.azure_tools = self.azure_server.list_tools()
                self.azure_session_active = True
                self.active_categories.add("azure")
                print(f"🔧 Loaded {len(self.azure_tools)} Azure tools")
            except Exception as e:
                print(f"❌ Failed to load Azure tools: {e}")
        
        elif category == "github" and self.github_server and not self.github_session_active:
            try:
                await self.github_server.initialize()
                self.github_tools = self.github_server.list_tools()
                self.github_session_active = True
                self.active_categories.add("github")
                print(f"🔧 Loaded {len(self.github_tools)} GitHub tools")
            except Exception as e:
                print(f"❌ Failed to load GitHub tools: {e}")
    
    def get_available_tools(self) -> List[Dict]:
        """Get formatted tools from all active categories"""
        available_tools = []
        
        if "azure" in self.active_categories and self.azure_server:
            available_tools.extend(self.azure_server.formatted_tools or [])
        
        if "github" in self.active_categories and self.github_server:
            available_tools.extend(self.github_server.formatted_tools or [])
        
        return available_tools
    
    async def call_tool(self, tool_name: str, arguments: Dict) -> str:
        """Route tool call to appropriate server"""
        # Check Azure tools
        if "azure" in self.active_categories and tool_name in [tool[0] for tool in self.azure_tools]:
            return await self.azure_server.call_tool(tool_name, arguments)
        
        # Check GitHub tools
        elif "github" in self.active_categories and tool_name in [tool[0] for tool in self.github_tools]:
            return await self.github_server.call_tool(tool_name, arguments)
        
        else:
            raise Exception(f"Tool {tool_name} not found in any active tool category")
    
    def get_tool_summary(self) -> str:
        """Get a summary of currently loaded tools"""
        summary = []
        if "azure" in self.active_categories:
            summary.append(f"Azure ({len(self.azure_tools)} tools)")
        if "github" in self.active_categories:
            summary.append(f"GitHub ({len(self.github_tools)} tools)")
        
        total_tools = len(self.get_available_tools())
        return f"{', '.join(summary)} - Total: {total_tools} tools"
    
    async def cleanup(self):
        """Clean up all active sessions"""
        if self.azure_session_active and self.azure_server:
            await self.azure_server.close()
        if self.github_session_active and self.github_server:
            await self.github_server.close()


async def run():
    # Initialize Azure OpenAI client
    client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version="2024-04-01-preview",
        azure_ad_token_provider=token_provider,
    )

    # Initialize dynamic tool manager
    tool_manager = DynamicToolManager()
    await tool_manager.initialize_servers()
    
    # Start conversational loop with dynamic tool loading
    await run_conversation_loop(client, tool_manager)


async def run_conversation_loop(client, tool_manager: DynamicToolManager):
    """Run the main conversation loop with dynamic tool loading"""
    messages = []
    print("\n🤖 Infrastructure Agent with Dynamic Tool Loading")
    print("💡 Tools will be loaded automatically based on your conversation context")
    print("📝 Type 'exit' to quit, 'tools' to see loaded tools\n")
    
    while True:
        try:
            user_input = input("Prompt: ")
            if user_input.lower() == 'exit':
                break
            elif user_input.lower() == 'tools':
                print(f"📦 Currently loaded: {tool_manager.get_tool_summary()}")
                continue
            
            # Analyze what tools might be needed for this conversation
            needed_categories = await tool_manager.analyze_conversation_context(messages, user_input)
            
            # Load any new tool categories that are needed
            newly_loaded = []
            for category in needed_categories:
                if category not in tool_manager.active_categories:
                    await tool_manager.load_category_tools(category)
                    newly_loaded.append(category)
            
            # Show what was loaded
            if newly_loaded:
                print(f"🔧 Loaded {', '.join(newly_loaded)} tools for this conversation")
            
            messages.append({"role": "user", "content": user_input})
            available_tools = tool_manager.get_available_tools()
            
            if not available_tools:
                print("⚠ No tools available. Please check your configuration.")
                continue
            
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
                        
                        # Use the tool manager to route the call
                        content = await tool_manager.call_tool(function_name, function_args)
                        
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
    
    # Cleanup
    await tool_manager.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
