"""Azure Infrastructure Agent using AutoGen AgentChat with MCP Integration

Prerequisites:
1. Install dependencies: pip install -r requirements.txt
2. Set environment variables:
   - AZURE_OPENAI_ENDPOINT: Your Azure OpenAI endpoint
   - AZURE_OPENAI_API_KEY or AZURE_OPENAI_KEY: Your Azure OpenAI API key
   - AZURE_API_VERSION: API version (default: 2024-12-01-preview)
3. Update azure_deployment names in the model client configurations below
"""

import asyncio
import os
import sys
import inspect
from typing import List, Sequence, Dict, Any, Callable
from dotenv import load_dotenv

# AutoGen imports
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_agentchat.ui import Console
from autogen_core.models import UserMessage
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams

# Load environment variables
load_dotenv()

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
AZURE_API_VERSION = os.getenv("AZURE_API_VERSION", "2024-12-01-preview")

# Model Configuration
AZURE_MODEL_NAME = os.getenv("AZURE_MODEL_NAME", "gpt-4.1")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-4.1")

# Configuration flags
ENABLE_MCP_TOOLS = os.getenv("ENABLE_MCP_TOOLS", "true").lower() == "true"

if not AZURE_OPENAI_ENDPOINT or not AZURE_API_KEY:
    raise ValueError("Missing required environment variables: AZURE_OPENAI_ENDPOINT and AZURE_API_KEY")

print(f"🤖 Using model: {AZURE_MODEL_NAME} (deployment: {AZURE_DEPLOYMENT_NAME})")

# Termination conditions
text_mention_termination = TextMentionTermination("TERMINATE")
max_messages_termination = MaxMessageTermination(max_messages=30)  # Reduced to prevent long loops
termination = text_mention_termination | max_messages_termination

# Create model clients for each agent
azure_model_client = AzureOpenAIChatCompletionClient(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_API_KEY,
    api_version=AZURE_API_VERSION,
    azure_deployment=AZURE_DEPLOYMENT_NAME,
    model=AZURE_MODEL_NAME,
)

github_model_client = AzureOpenAIChatCompletionClient(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_API_KEY,
    api_version=AZURE_API_VERSION,
    azure_deployment=AZURE_DEPLOYMENT_NAME,
    model=AZURE_MODEL_NAME,
)

coordinator_model_client = AzureOpenAIChatCompletionClient(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_API_KEY,
    api_version=AZURE_API_VERSION,
    azure_deployment=AZURE_DEPLOYMENT_NAME,
    model=AZURE_MODEL_NAME,
)

# Define the agents
coordinator_agent = AssistantAgent(
    name="CoordinatorAgent",
    description="Coordinates tasks between Azure and GitHub agents.",
    model_client=coordinator_model_client,
    system_message="""
    You are a coordinator agent for Azure infrastructure and GitHub analysis.
    Your team members are:
        AzureAgent: Handles Azure infrastructure queries and commands
        GitHubAgent: Handles GitHub repository analysis

    IMPORTANT: Avoid asking for clarification - be proactive and decisive.

    For ambiguous requests like "list subscriptions" or "list subs":
    - DEFAULT ACTION: List BOTH Azure and GitHub subscriptions
    - Assign both agents simultaneously: "AzureAgent: list Azure subscriptions" AND "GitHubAgent: list GitHub repositories"
    - Present unified results clearly labeled by platform

    When assigning tasks, use this format:
    1. <agent> : <task>

    For Azure queries (subscriptions, VNets, resources), assign to AzureAgent.
    For GitHub queries (repositories, issues, PRs), assign to GitHubAgent.
    For ambiguous requests, assign to BOTH agents.

    Only say "TERMINATE" when all assigned tasks have been completed by other agents and you have provided a final summary.
    """,
)

azure_agent = AssistantAgent(
    name="AzureAgent",
    description="An agent for Azure infrastructure analysis and management.",
    tools=None,  # Will be set after connecting to MCP server
    model_client=azure_model_client,
    system_message="""
    You are an Azure infrastructure expert with access to live Azure MCP tools.

    MANDATORY: You MUST use your available Azure MCP tools to get actual data from the user's Azure account. 
    
    NEVER provide generic instructions about Azure CLI, PowerShell, or Portal usage.
    NEVER provide example or fictional data.
    ALWAYS call the actual MCP tools available to you.

    When asked about Azure subscriptions:
    1. IMMEDIATELY call the "subscription" function/tool that is available to you
    2. Use arguments like {"command": "list", "parameters": {}} or {"learn": true}
    3. Wait for the real results from the tool call
    4. Format the actual returned data as a clean table:
       | Subscription Name | Subscription ID | State | Tenant ID |
    5. Present only the real data returned by the tool

    For any Azure request:
    - First call the appropriate MCP tool (subscription, group, storage, etc.)
    - Use the real data returned
    - Format results clearly
    - Never suggest manual methods or provide generic instructions

    You have access to live Azure MCP tools. Use them immediately for every request.
    """,
)

github_agent = AssistantAgent(
    name="GitHubAgent",
    description="An agent for GitHub repository analysis.",
    tools=None,  # Will be set after connecting to MCP server
    model_client=github_model_client,
    system_message="""
    You are a GitHub repository analysis expert.

    When asked about repositories:
    1. List repositories with details
    2. Analyze code structure
    3. Review issues and pull requests
    4. Provide insights on repository health

    Always use actual data from GitHub tools.
    """,
)

# Create user proxy for human-in-the-loop when needed
user_proxy = UserProxyAgent(
    name="HumanUser",
    description="Human user who can provide clarification when needed."
)

# Define the team with human-in-the-loop capability
team = MagenticOneGroupChat(
    participants=[coordinator_agent, azure_agent, github_agent, user_proxy],
    model_client=coordinator_model_client,
    termination_condition=termination,
)

class MCPToolManager:
    """Manages MCP servers and tools with proper lifecycle management"""
    
    def __init__(self):
        self.azure_server = None
        self.github_server = None
        self.azure_tools = []
        self.github_tools = []
    
    async def initialize(self):
        """Initialize MCP servers and extract tools"""
        if not ENABLE_MCP_TOOLS:
            print("🚫 MCP tools disabled via ENABLE_MCP_TOOLS=false")
            return [], []
        
        try:
            # Add the agent directory to the path
            import sys
            agent_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'agent')
            if agent_dir not in sys.path:
                sys.path.append(agent_dir)
            
            from azure_mcp_server import AzureMCPServer
            from github_mcp_server import GitHubMCPServer
            
            # Initialize Azure MCP server
            try:
                print("🔄 Creating Azure MCP server...")
                self.azure_server = AzureMCPServer()
                
                print("🔄 Initializing Azure MCP server...")
                await self.azure_server.initialize()
                
                print(f"🔄 Azure server initialized. Has formatted_tools: {hasattr(self.azure_server, 'formatted_tools')}")
                if hasattr(self.azure_server, 'formatted_tools'):
                    print(f"🔄 Raw formatted_tools count: {len(self.azure_server.formatted_tools) if self.azure_server.formatted_tools else 0}")
                
                # Convert MCP tools to AutoGen-compatible functions
                if hasattr(self.azure_server, 'formatted_tools') and self.azure_server.formatted_tools:
                    print("🔄 Converting MCP tools to AutoGen functions...")
                    self.azure_tools = await self._convert_mcp_tools_to_functions(
                        self.azure_server.formatted_tools, "Azure"
                    )
                    print(f"🔄 Converted {len(self.azure_tools)} Azure tools")
                else:
                    print("❌ No formatted_tools available from Azure MCP server")
                    self.azure_tools = []
                    
                print(f"✅ Azure MCP: {len(self.azure_tools)} tools loaded")
            except Exception as e:
                print(f"❌ Azure MCP initialization failed: {e}")
                import traceback
                traceback.print_exc()
                print("Continuing without Azure MCP tools...")
                self.azure_tools = []
            
            # Initialize GitHub MCP server
            try:
                self.github_server = GitHubMCPServer()
                await self.github_server.initialize()
                
                # Convert MCP tools to AutoGen-compatible functions
                if hasattr(self.github_server, 'formatted_tools') and self.github_server.formatted_tools:
                    self.github_tools = await self._convert_mcp_tools_to_functions(
                        self.github_server.formatted_tools, "GitHub"
                    )
                print(f"✅ GitHub MCP: {len(self.github_tools)} tools loaded")
            except Exception as e:
                print(f"❌ GitHub MCP initialization failed: {e}")
                print("Continuing without GitHub MCP tools...")
            
            return self.azure_tools, self.github_tools
            
        except Exception as e:
            print(f"❌ Could not import MCP servers: {e}")
            print("Continuing without MCP tools...")
            return [], []
    
    async def _convert_mcp_tools_to_functions(self, mcp_tools, server_type):
        """Convert MCP tools to AutoGen-compatible functions"""
        functions = []
        server = self.azure_server if server_type == "Azure" else self.github_server
        
        for tool_spec in mcp_tools:
            try:
                # Extract function information from the MCP tool specification
                if "function" in tool_spec:
                    func_info = tool_spec["function"]
                    tool_name = func_info["name"]
                    tool_description = func_info["description"]
                    tool_parameters = func_info.get("parameters", {})
                    
                    # Create a wrapper function for the MCP tool - fix closure issues
                    def create_tool_wrapper(name, description, server_ref, params):
                        async def tool_wrapper(**kwargs):
                            """Dynamically created tool wrapper for MCP tool"""
                            try:
                                print(f"🔧 Calling {server_type} MCP tool: {name}")
                                print(f"📝 Arguments: {kwargs}")
                                
                                # Call the MCP server directly using the same pattern as main_simple.py
                                result = await server_ref.call_tool(name, kwargs)
                                
                                print(f"✅ Tool '{name}' returned {len(str(result))} characters")
                                print(f"📤 Result preview: {str(result)[:200]}...")
                                
                                return result
                            except Exception as e:
                                error_msg = f"Error calling {name}: {str(e)}"
                                print(f"❌ {error_msg}")
                                return error_msg
                        
                        # Set function metadata for AutoGen
                        tool_wrapper.__name__ = name
                        tool_wrapper.__doc__ = description
                        tool_wrapper._autogen_tool_schema = {
                            "name": name,
                            "description": description,
                            "parameters": params
                        }
                        return tool_wrapper
                    
                    # Create the wrapper function with fixed closure
                    wrapper_func = create_tool_wrapper(tool_name, tool_description, server, tool_parameters)
                    functions.append(wrapper_func)
                    
            except Exception as e:
                print(f"⚠️  Warning: Could not convert {server_type} tool: {e}")
        
        return functions
    
    async def cleanup(self):
        """Clean up MCP servers"""
        try:
            if self.azure_server and hasattr(self.azure_server, 'close'):
                await self.azure_server.close()
        except Exception as e:
            print(f"⚠️  Warning during Azure MCP cleanup: {e}")
        
        try:
            if self.github_server and hasattr(self.github_server, 'close'):
                await self.github_server.close()
        except Exception as e:
            print(f"⚠️  Warning during GitHub MCP cleanup: {e}")

# Global MCP manager
mcp_manager = MCPToolManager()

async def create_mcp_tools():
    """Create MCP tools using the manager"""
    return await mcp_manager.initialize()

async def main():
    """Main entry point"""
    print("Starting Azure Infrastructure Agent Team...")
    print("-" * 50)
    
    # Check Azure authentication environment variables
    azure_auth_vars = {
        "AZURE_CLIENT_ID": os.getenv("AZURE_CLIENT_ID"),
        "AZURE_CLIENT_SECRET": os.getenv("AZURE_CLIENT_SECRET"), 
        "AZURE_TENANT_ID": os.getenv("AZURE_TENANT_ID"),
        "AZURE_SUBSCRIPTION_ID": os.getenv("AZURE_SUBSCRIPTION_ID")
    }
    
    print("🔐 Checking Azure authentication environment variables:")
    for var_name, var_value in azure_auth_vars.items():
        status = "✅ Set" if var_value else "❌ Missing"
        print(f"   {var_name}: {status}")
    
    missing_vars = [name for name, value in azure_auth_vars.items() if not value]
    if missing_vars:
        print(f"⚠️  Missing Azure auth variables: {missing_vars}")
        print("   This may cause Azure MCP tools to fail")
    else:
        print("✅ All Azure auth variables are set")
    
    print("-" * 50)
    
    try:
        # Get MCP tools with timeout
        azure_tools, github_tools = await asyncio.wait_for(
            create_mcp_tools(), timeout=30.0
        )
        
        # Set tools for agents with debugging
        azure_agent.tools = azure_tools
        github_agent.tools = github_tools
        
        print(f"Total tools available: Azure={len(azure_tools)}, GitHub={len(github_tools)}")
        
        # Debug: Show some tool names
        if azure_tools:
            tool_names = [getattr(tool, '__name__', str(tool)) for tool in azure_tools[:5]]
            print(f"🔧 Azure tools assigned: {tool_names}...")
            
            # Check if tools are callable
            for i, tool in enumerate(azure_tools[:3]):
                print(f"   Tool {i}: {getattr(tool, '__name__', 'unknown')} - callable: {callable(tool)}")
            
            # Test if subscription tool is available
            subscription_tools = [tool for tool in azure_tools if getattr(tool, '__name__', '') == 'subscription']
            if subscription_tools:
                print(f"✅ Subscription tool found and assigned")
                
                # Quick test call to verify it works
                try:
                    print("🧪 Testing subscription tool...")
                    test_result = await subscription_tools[0](learn=True)
                    print(f"🧪 Test result: {str(test_result)[:200]}...")
                except Exception as e:
                    print(f"❌ Test failed: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("❌ Subscription tool NOT found in Azure tools")
                if azure_tools:
                    print(f"   Available tool names: {[getattr(t, '__name__', str(t)) for t in azure_tools]}")
                
        else:
            print("❌ NO Azure tools were created!")
            
        if github_tools:
            tool_names = [getattr(tool, '__name__', str(tool)) for tool in github_tools[:5]]
            print(f"🔧 GitHub tools assigned: {tool_names}...")
        else:
            print("❌ NO GitHub tools were created!")
            
        # Check agent tool assignment
        print(f"🔍 Azure agent has {len(azure_agent.tools) if azure_agent.tools else 0} tools assigned")
        print(f"🔍 GitHub agent has {len(github_agent.tools) if github_agent.tools else 0} tools assigned")
        
        print("-" * 50)
        
        while True:
            try:
                # Get task from user input
                task = input("Enter your request (or 'quit' to exit): ")
                
                if task.lower() in ['quit', 'exit', 'bye']:
                    print("Goodbye!")
                    break
                
                print(f"\nProcessing: {task}")
                print("-" * 50)
                
                # Use streaming for real-time feedback
                try:
                    print("🚀 Starting streaming execution...")
                    
                    # Create the stream
                    stream = team.run_stream(task=task)
                    
                    # Process messages as they come in
                    message_count = 0
                    async for message in stream:
                        message_count += 1
                        
                        # Handle different message types
                        if hasattr(message, 'source') and hasattr(message, 'content'):
                            source = message.source
                            content = message.content
                            
                            # Show tool calls clearly
                            if "calling" in content.lower() or "tool" in content.lower():
                                print(f"\n🔧 [{source}]: {content}")
                            else:
                                print(f"\n[{source}]: {content}")
                                
                        elif hasattr(message, 'messages'):
                            # This might be a TaskResult
                            print(f"\n🎯 Task completed with {len(message.messages)} total messages")
                            break
                        else:
                            # Fallback for other message types - show more detail for debugging
                            msg_type = type(message).__name__
                            msg_content = str(message)[:200] + "..." if len(str(message)) > 200 else str(message)
                            print(f"\n📨 {msg_type}: {msg_content}")
                        
                        # Prevent infinite loops
                        if message_count > 100:
                            print("⚠️  Stopping after 100 messages to prevent infinite loop")
                            break
                    
                    print("\n✅ Streaming completed")
                    
                except Exception as e:
                    print(f"❌ Streaming failed: {e}")
                    import traceback
                    traceback.print_exc()
                
            except KeyboardInterrupt:
                print("\n\n⏹️  Interrupted by user")
                break
                
    except asyncio.TimeoutError:
        print("❌ MCP initialization timed out after 30 seconds")
    except KeyboardInterrupt:
        print("\n\n⏹️  Shutting down...")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up resources
        print("🧹 Cleaning up...")
        
        # Clean up MCP servers first
        try:
            await mcp_manager.cleanup()
        except Exception as e:
            print(f"⚠️  Warning during MCP cleanup: {e}")
        
        # Clean up model clients
        for client_name, client in [("azure", azure_model_client), ("github", github_model_client), ("coordinator", coordinator_model_client)]:
            try:
                if hasattr(client, 'close'):
                    await client.close()
            except (asyncio.CancelledError, RuntimeError, ConnectionError):
                # Suppress expected shutdown errors
                pass
            except Exception as e:
                print(f"⚠️  Warning during {client_name} client shutdown: {e}")
        print("✅ Shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (asyncio.CancelledError, RuntimeError, ValueError) as e:
        # Suppress async shutdown errors from MCP/AutoGen/anyio
        if any(msg in str(e) for msg in ["cancel scope", "task_done", "CancelledError"]):
            pass
        else:
            print(f"Shutdown error: {e}")
    except KeyboardInterrupt:
        print("\nShutdown interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")