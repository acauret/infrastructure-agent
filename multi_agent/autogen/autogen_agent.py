"""Azure Infrastructure Agent using AutoGen AgentChat with MCP Integration"""

import asyncio
import os
import sys
from typing import List, Sequence
from dotenv import load_dotenv

# AutoGen imports
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage
from autogen_agentchat.teams import MagenticOneGroupChat, SelectorGroupChat
from autogen_agentchat.ui import Console
from autogen_core.models import UserMessage, SystemMessage, AssistantMessage
from autogen_ext.models.azure import AzureAIChatCompletionClient
from azure.core.credentials import AzureKeyCredential

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
azure_model_client = AzureAIChatCompletionClient(
    endpoint=AZURE_OPENAI_ENDPOINT,
    credential=AzureKeyCredential(AZURE_API_KEY),
    api_version=AZURE_API_VERSION,
    model_info={
        "json_output": True,
        "function_calling": True,
        "vision": False,
        "family": "gpt-4o",
        "structured_output": False,
    },
)

github_model_client = AzureAIChatCompletionClient(
    endpoint=AZURE_OPENAI_ENDPOINT,
    credential=AzureKeyCredential(AZURE_API_KEY),
    api_version=AZURE_API_VERSION,
    model_info={
        "json_output": True,
        "function_calling": True,
        "vision": False,
        "family": "gpt-4o",
        "structured_output": False,
    },
)

coordinator_model_client = AzureAIChatCompletionClient(
    endpoint=AZURE_OPENAI_ENDPOINT,
    credential=AzureKeyCredential(AZURE_API_KEY),
    api_version=AZURE_API_VERSION,
    model_info={
        "json_output": True,
        "function_calling": True,
        "vision": False,
        "family": "gpt-4o",
        "structured_output": False,
    },
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
    emit_team_events=True,
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
        
        # Initialize Azure MCP server
        try:
            azure_server = AzureMCPServer()
            await azure_server.initialize()
            if hasattr(azure_server, 'formatted_tools') and azure_server.formatted_tools:
                azure_tools = [tool["function"] for tool in azure_server.formatted_tools]
            print(f"✅ Azure MCP: {len(azure_tools)} tools loaded")
        except Exception as e:
            print(f"❌ Azure MCP initialization failed: {e}")
        
        # Initialize GitHub MCP server
        try:
            github_server = GitHubMCPServer()
            await github_server.initialize()
            if hasattr(github_server, 'formatted_tools') and github_server.formatted_tools:
                github_tools = [tool["function"] for tool in github_server.formatted_tools]
            print(f"✅ GitHub MCP: {len(github_tools)} tools loaded")
        except Exception as e:
            print(f"❌ GitHub MCP initialization failed: {e}")
        
        return azure_tools, github_tools
        
    except Exception as e:
        print(f"❌ Could not import MCP servers: {e}")
        print("Continuing without MCP tools...")
        return [], []

async def main():
    """Main entry point"""
    print("Starting Azure Infrastructure Agent Team...")
    print("-" * 50)
    
    # Get MCP tools
    azure_tools, github_tools = await create_mcp_tools()
    
    # Set tools for agents
    azure_agent.tools = azure_tools
    github_agent.tools = github_tools
    
    print(f"Total tools available: Azure={len(azure_tools)}, GitHub={len(github_tools)}")
    print("-" * 50)
    
    # Get task from user input
    task = input("Enter your request (or 'quit' to exit): ")
    
    if task.lower() in ['quit', 'exit', 'bye']:
        print("Goodbye!")
        return
    
    print(f"\nProcessing: {task}")
    print("-" * 50)
    
    try:
        async for message in team.run_stream(task=task):
            # Skip TaskResult messages or handle them differently
            if hasattr(message, 'messages') and not hasattr(message, 'source'):
                # This is likely a TaskResult - you can access the final result here
                print(f"[TASK COMPLETED] Final result with {len(message.messages)} messages")
                continue
                
            print(
                f"[{getattr(message, 'source', 'Unknown')}] ({getattr(message, 'type', type(message).__name__)}):\n{getattr(message, 'content', message)}\n"
            )
    
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    except Exception as e:
        print(f"\nError: {e}")
    
    finally:
        # Clean up model clients, suppressing async shutdown errors
        for client in [azure_model_client, github_model_client, coordinator_model_client]:
            try:
                await client.close()
            except (asyncio.CancelledError, RuntimeError):
                pass
            except Exception as e:
                print(f"Warning during shutdown: {e}")
        print("Shutdown complete")

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