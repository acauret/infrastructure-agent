"""Azure Infrastructure Agent using AutoGen 0.7.2 with MCP Integration

Prerequisites:
1. Install dependencies: pip install -r requirements.txt
2. Set environment variables:
   - AZURE_OPENAI_ENDPOINT: Your Azure OpenAI endpoint
   - AZURE_OPENAI_API_KEY or AZURE_OPENAI_KEY: Your Azure OpenAI API key
   - AZURE_API_VERSION: API version (default: 2024-12-01-preview)
   - GITHUB_PERSONAL_ACCESS_TOKEN: Your GitHub token for GitHub MCP
3. Update azure_deployment names in the model client configurations below
"""

import asyncio
import os
import sys
from typing import List, Optional
from dotenv import load_dotenv

# AutoGen 0.7.2 imports
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination, TextMessageTermination
from autogen_agentchat.teams import MagenticOneGroupChat, RoundRobinGroupChat
from autogen_agentchat.ui import Console
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
max_messages_termination = MaxMessageTermination(max_messages=30)
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

def create_mcp_server_params():
    """Create MCP server parameters"""
    server_params = []
    
    if not ENABLE_MCP_TOOLS:
        print("🚫 MCP tools disabled via ENABLE_MCP_TOOLS=false")
        return server_params
    
    # Azure MCP server parameters
    try:
        print("🔄 Creating Azure MCP server params...")
        azure_server_params = StdioServerParams(
            command="npx",
            args=["-y", "@azure/mcp@latest", "server", "start"]
        )
        server_params.append(azure_server_params)
        print("✅ Azure MCP server params created")
    except Exception as e:
        print(f"❌ Azure MCP server params creation failed: {e}")
    
    # GitHub MCP server parameters
    try:
        github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        if github_token:
            print("🔄 Creating GitHub MCP server params...")
            github_server_params = StdioServerParams(
                command="docker",
                args=[
                    "run", "-i", "--rm",
                    "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
                    "ghcr.io/github/github-mcp-server",
                    "stdio"
                ]
            )
            server_params.append(github_server_params)
            print("✅ GitHub MCP server params created")
        else:
            print("❌ GITHUB_PERSONAL_ACCESS_TOKEN not set - skipping GitHub MCP")
    except Exception as e:
        print(f"❌ GitHub MCP server params creation failed: {e}")
    
    return server_params

async def run_agent_system(workbenches):
    """Run the agent system with optional MCP workbenches"""
    
    # Define the main Azure agent
    azure_agent = AssistantAgent(
        name="AzureAgent",
        description="An agent for Azure infrastructure analysis and management.",
        model_client=azure_model_client,
        workbench=workbenches[0] if workbenches else None,  # Use first workbench (Azure)
        model_client_stream=True,
        max_tool_iterations=10,
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

    # Simple team with just the Azure agent for now
    team = RoundRobinGroupChat(
        [azure_agent],
        termination_condition=TextMessageTermination(source="AzureAgent"),
    )

    print("✅ Agent team created successfully")
    print(f"🔍 MCP workbenches: {'✅ Available' if workbenches else '❌ Not available'}")
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
                
                # Use Console for clean output - following the exact pattern from the example
                await Console(team.run_stream(task=task))
                
                print("\n✅ Streaming completed")
                
            except Exception as e:
                print(f"❌ Streaming failed: {e}")
                import traceback
                traceback.print_exc()
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Interrupted by user")
            break

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
        # Create MCP server parameters
        print("🔄 Creating MCP server parameters...")
        server_params_list = create_mcp_server_params()
        
        if not server_params_list:
            print("❌ No MCP servers configured - running without MCP tools")
            workbenches = None
        else:
            # Create list of workbenches for multiple MCP servers
            workbenches = [McpWorkbench(params) for params in server_params_list]
            print(f"✅ Created {len(workbenches)} MCP workbenches")
        
        # Use context manager for proper resource management
        if workbenches:
            async with workbenches[0] if len(workbenches) == 1 else workbenches[0]:  # Simplified for demo
                await run_agent_system(workbenches)
        else:
            await run_agent_system(None)
                
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
        
        # Clean up model clients
        for client_name, client in [("azure", azure_model_client)]:
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
        # Suppress async shutdown errors from MCP/AutoGen
        if any(msg in str(e) for msg in ["cancel scope", "task_done", "CancelledError"]):
            pass
        else:
            print(f"Shutdown error: {e}")
    except KeyboardInterrupt:
        print("\nShutdown interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
