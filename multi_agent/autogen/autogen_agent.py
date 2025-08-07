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
from typing import List, Sequence
from dotenv import load_dotenv

# AutoGen imports
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_agentchat.ui import Console
from autogen_core.models import UserMessage
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

# Load environment variables
load_dotenv()

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
AZURE_API_VERSION = os.getenv("AZURE_API_VERSION", "2024-12-01-preview")

if not AZURE_OPENAI_ENDPOINT or not AZURE_API_KEY:
    raise ValueError("Missing required environment variables: AZURE_OPENAI_ENDPOINT and AZURE_API_KEY")

# Termination conditions
text_mention_termination = TextMentionTermination("TERMINATE")
max_messages_termination = MaxMessageTermination(max_messages=50)
termination = text_mention_termination | max_messages_termination

# Create model clients for each agent
azure_model_client = AzureOpenAIChatCompletionClient(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_API_KEY,
    api_version=AZURE_API_VERSION,
    azure_deployment="gpt-4o",  # Replace with your actual deployment name
    model="gpt-4o",
)

github_model_client = AzureOpenAIChatCompletionClient(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_API_KEY,
    api_version=AZURE_API_VERSION,
    azure_deployment="gpt-4o",  # Replace with your actual deployment name
    model="gpt-4o",
)

coordinator_model_client = AzureOpenAIChatCompletionClient(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_API_KEY,
    api_version=AZURE_API_VERSION,
    azure_deployment="gpt-4o",  # Replace with your actual deployment name
    model="gpt-4o",
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

    You plan and delegate tasks - you do not execute them yourself.

    When assigning tasks, use this format:
    1. <agent> : <task>

    For Azure queries (subscriptions, VNets, resources), assign to AzureAgent.
    For GitHub queries (repositories, issues, PRs), assign to GitHubAgent.

    Only say "TERMINATE" when all assigned tasks have been completed by other agents and you have provided a final summary.
    """,
)

azure_agent = AssistantAgent(
    name="AzureAgent",
    description="An agent for Azure infrastructure analysis and management.",
    tools=None,  # Will be set after connecting to MCP server
    model_client=azure_model_client,
    system_message="""
    You are an Azure infrastructure expert assistant.

    When asked about Azure resources:
    1. First get subscription details
    2. List resource groups and resources
    3. For VNets, show all details including address spaces and subnets
    4. Provide clear, concise summaries

    Always execute the necessary tools to get real data. Never make up information.
    Format responses clearly with the actual data retrieved.
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

# Define the team
team = MagenticOneGroupChat(
    participants=[coordinator_agent, azure_agent, github_agent],
    model_client=coordinator_model_client,
    termination_condition=termination,
)

async def create_mcp_tools():
    """Create MCP tools for Azure and GitHub"""
    try:
        # Add the agent directory to the path so we can import MCP servers
        import sys
        agent_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'agent')
        if agent_dir not in sys.path:
            sys.path.append(agent_dir)
        
        from azure_mcp_server import AzureMCPServer
        from github_mcp_server import GitHubMCPServer
        
        azure_tools = []
        github_tools = []
        
        # Initialize Azure MCP server with better error handling
        try:
            azure_server = AzureMCPServer()
            await azure_server.initialize()
            if hasattr(azure_server, 'formatted_tools') and azure_server.formatted_tools:
                azure_tools = [tool["function"] for tool in azure_server.formatted_tools]
            print(f"✅ Azure MCP: {len(azure_tools)} tools loaded")
        except Exception as e:
            print(f"❌ Azure MCP initialization failed: {e}")
            print("Continuing without Azure MCP tools...")
        
        # Initialize GitHub MCP server with better error handling
        try:
            github_server = GitHubMCPServer()
            await github_server.initialize()
            if hasattr(github_server, 'formatted_tools') and github_server.formatted_tools:
                github_tools = [tool["function"] for tool in github_server.formatted_tools]
            print(f"✅ GitHub MCP: {len(github_tools)} tools loaded")
        except Exception as e:
            print(f"❌ GitHub MCP initialization failed: {e}")
            print("Continuing without GitHub MCP tools...")
        
        return azure_tools, github_tools
        
    except Exception as e:
        print(f"❌ Could not import MCP servers: {e}")
        print("Continuing without MCP tools...")
        return [], []

async def main():
    """Main entry point"""
    print("Starting Azure Infrastructure Agent Team...")
    print("-" * 50)
    
    try:
        # Get MCP tools with timeout
        azure_tools, github_tools = await asyncio.wait_for(
            create_mcp_tools(), timeout=30.0
        )
        
        # Set tools for agents
        azure_agent.tools = azure_tools
        github_agent.tools = github_tools
        
        print(f"Total tools available: Azure={len(azure_tools)}, GitHub={len(github_tools)}")
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
                
                # Run the team with timeout
                result = await asyncio.wait_for(
                    team.run(task=task), timeout=300.0  # 5 minute timeout
                )
                
                print(f"\n=== Task Result ===")
                if hasattr(result, 'messages') and result.messages:
                    for i, message in enumerate(result.messages):
                        source = getattr(message, 'source', 'Unknown')
                        content = getattr(message, 'content', str(message))
                        print(f"[{i+1}] {source}: {content}")
                else:
                    print("No messages returned")
                print("==================\n")
                
            except asyncio.TimeoutError:
                print("⏰ Task timed out after 5 minutes")
            except KeyboardInterrupt:
                print("\n\n⏹️  Interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error processing task: {e}")
                # Continue with the loop instead of breaking
                
    except asyncio.TimeoutError:
        print("❌ MCP initialization timed out after 30 seconds")
    except KeyboardInterrupt:
        print("\n\n⏹️  Shutting down...")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up model clients with better error handling
        print("🧹 Cleaning up...")
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