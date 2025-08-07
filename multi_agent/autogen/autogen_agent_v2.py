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
from contextlib import AsyncExitStack
import os
from typing import List, Optional
from dotenv import load_dotenv

# AutoGen 0.7.2 imports
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import MagenticOneGroupChat
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

# Create model client (shared across agents)
azure_model_client = AzureOpenAIChatCompletionClient(
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
    
    # GitHub MCP server parameters (with environment variables)
    try:
        github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        if github_token:
            print("🔄 Creating GitHub MCP server params...")
            print(f"🔑 GitHub token found: {github_token[:8]}...")
            
            # Create environment with GitHub token
            current_env = os.environ.copy()
            current_env["GITHUB_PERSONAL_ACCESS_TOKEN"] = github_token
            
            # Try npx-based GitHub MCP server with proper environment
            github_server_params = StdioServerParams(
                command="npx",
                args=[
                    "github-mcp-custom",
                    "stdio"
                ],
                env=current_env  # Pass environment variables including the GitHub token
            )
            server_params.append(github_server_params)
            print("✅ GitHub MCP server params created (npx-based with token)")
        else:
            print("❌ GITHUB_PERSONAL_ACCESS_TOKEN not set - skipping GitHub MCP")
    except Exception as e:
        print(f"❌ GitHub MCP server params creation failed: {e}")
        print("🔄 Continuing without GitHub MCP server")

    # Playwright MCP server (web browsing)
    try:
        print("🔄 Creating Playwright MCP server params...")
        pw_params = StdioServerParams(
            command="npx",
            args=["@playwright/mcp@latest", "--headless"],
        )
        server_params.append(pw_params)
        print("✅ Playwright MCP server params created")
    except Exception as e:
        print(f"❌ Playwright MCP server params creation failed: {e}")
    
    return server_params

async def run_agent_system(workbenches: Optional[List[McpWorkbench]]):
    """Run the agent system with optional MCP workbenches"""
    
    print("✅ MagenticOne agent team setup ready")
    print(f"🔍 MCP workbenches: {'✅ Available' if workbenches else '❌ Not available'}")
    has_github = bool(workbenches and len(workbenches) > 1)
    # Playwright index depends on whether GitHub workbench is present
    has_playwright = bool(workbenches and ((has_github and len(workbenches) > 2) or (not has_github and len(workbenches) > 1)))
    has_infracoder = bool(has_github)
    if has_github:
        print("📱 GitHub agent: ✅ Enabled")
    else:
        print("📱 GitHub agent: ❌ Not available (check GITHUB_PERSONAL_ACCESS_TOKEN)")
    if has_playwright:
        print("🌐 Playwright agent: ✅ Enabled")
    else:
        print("🌐 Playwright agent: ❌ Not available")
    if has_infracoder:
        print("🧩 InfraCoder agent: ✅ Enabled")
    else:
        print("🧩 InfraCoder agent: ❌ Not available (requires GitHub MCP)")
    print("-" * 50)

    # Use MagenticOneGroupChat (as originally requested)
    request_count = 0
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
                
                # Create fresh agents for each request with unique names
                request_count += 1
                # Determine available team members dynamically
                team_description = "AzureAgent: Handles Azure infrastructure queries and commands"
                if has_github:
                    team_description += "\n                        GitHubAgent: Handles GitHub repository analysis"
                if has_infracoder:
                    team_description += "\n                        InfraCoderAgent: Handles Terraform/Bicep coding tasks with branching and PRs"
                
                coordinator_agent = AssistantAgent(
                    name=f"MagenticOneOrchestrator_{request_count}",
                    description="Coordinates tasks between available agents.",
                    model_client=azure_model_client,
                    system_message=f"""
                    You are a MagenticOne coordinator agent for Azure infrastructure and analysis.
                    Your available team members are:
                        {team_description}

                    IMPORTANT: Avoid asking for clarification - be proactive and decisive.

                    For ambiguous requests like "list subscriptions" or "list subs":
                    - Focus on Azure subscriptions (always available)
                    - If GitHub agent is available and user asks about repos, use GitHubAgent
                    - Assign tasks clearly: "AzureAgent: list Azure subscriptions"

                    When assigning tasks, use this format:
                    1. @AzureAgent: <specific Azure task>
                    2. @GitHubAgent: <specific GitHub task> (only if GitHub agent is available)
                    3. @InfraCoderAgent: <specific coding task for Terraform/Bicep and repo changes> (only if InfraCoder agent is available)

                    For Azure queries (subscriptions, VNets, resources), assign to AzureAgent.
                    {"For GitHub queries (repositories, issues, PRs), assign to GitHubAgent." if has_github else "GitHub queries: Explain that GitHub tools are not currently available."}
                    
                    IMPORTANT: Only assign tasks to agents that are actually available in your team.

                    Only say "TERMINATE" when all assigned tasks have been completed by other agents and you have provided a final summary.
                    """,
                )
                
                azure_agent = AssistantAgent(
                    name=f"AzureAgent_{request_count}",
                    description="An agent for Azure infrastructure analysis and management.",
                    model_client=azure_model_client,
                    workbench=workbenches[0] if workbenches else None,
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
                    
                    When the MagenticOneOrchestrator assigns you a task, acknowledge and execute it immediately.
                    """,
                )

                user_proxy = UserProxyAgent(
                    name=f"HumanUser_{request_count}",
                    description="Human user who can provide clarification when needed."
                )

                # Create participants list
                participants = [coordinator_agent, azure_agent, user_proxy]
                
                # Add GitHub agent if available (with MCP error handling)
                if has_github:
                    try:
                        github_agent = AssistantAgent(
                            name=f"GitHubAgent_{request_count}",
                            description="An agent for GitHub repository analysis.",
                            model_client=azure_model_client,
                            workbench=workbenches[1],
                            model_client_stream=True,
                            max_tool_iterations=10,
                            system_message="""
                            You are a GitHub repository analysis expert.

                            When asked about repositories:
                            1. List repositories with details
                            2. Analyze code structure
                            3. Review issues and pull requests
                            4. Provide insights on repository health

                            Always use actual data from GitHub tools when available.
                            If GitHub MCP tools are not accessible, politely explain the limitation.
                            
                            When the MagenticOneOrchestrator assigns you a task, acknowledge and execute it immediately.
                            """,
                        )
                        participants.insert(2, github_agent)
                    except Exception as github_error:
                        print(f"⚠️  GitHub agent creation failed: {github_error}")
                        print("🔄 Continuing with Azure-only team")
                        has_github = False

                # Add InfraCoder agent if available (uses GitHub + optional Playwright)
                if has_infracoder:
                    try:
                        pw_index = 2 if has_github else 1
                        coder_workbenches = [workbenches[1]]
                        if has_playwright:
                            coder_workbenches.append(workbenches[pw_index])
                        infracoder_agent = AssistantAgent(
                            name=f"InfraCoderAgent_{request_count}",
                            description="An agent for Terraform/Bicep coding tasks: browse AVM modules, analyze repos, create branches and PRs.",
                            model_client=azure_model_client,
                            workbench=coder_workbenches,
                            model_client_stream=True,
                            max_tool_iterations=15,
                            system_message="""
                            You are an infrastructure-as-code engineer specializing in Terraform and Bicep.
                            Your responsibilities:
                            - Discover and reference latest Azure Verified Modules (AVM):
                              Terraform: https://azure.github.io/Azure-Verified-Modules/indexes/terraform/tf-resource-modules/
                              Bicep:    https://azure.github.io/Azure-Verified-Modules/indexes/bicep/bicep-resource-modules/
                              Use the Playwright MCP tools to browse these pages when needed and extract authoritative guidance.
                            - Analyze a target repository (structure, modules, conventions). Use GitHub MCP tools to search, read files, and inspect branches.
                            - Implement changes following best practices (naming, tags, variables/parameters, README updates).
                            - Workflow for repo changes (via GitHub MCP tools):
                              1) Create a new branch named: feature/avm-<resource>-<yyyyMMdd>-<shortid>
                              2) Add or modify files with minimal diffs and clear structure.
                              3) Commit with conventional message, e.g.: feat(<area>): add <resource> with AVM best practices
                              4) Open a Pull Request with a concise summary, checklist, and references to AVM docs.
                            - Validate: plan or lint if tools are available; otherwise explain validation steps for the maintainer.
                            - If required inputs are missing (repository, paths, resource details), propose a minimal plan and ask only for the essential missing fields.

                            Important rules:
                            - Prefer AVM modules where suitable; otherwise follow Microsoft Azure Terraform/Bicep guidance.
                            - Do not include secrets. Use variables/parameters and document them.
                            - Keep edits focused; avoid unrelated refactors unless explicitly requested.
                            - Use available MCP tools only; do not invent tool names.
                            """,
                        )
                        participants.insert(2, infracoder_agent)
                    except Exception as coder_error:
                        print(f"⚠️  InfraCoder agent creation failed: {coder_error}")
                        has_infracoder = False

                # Add Playwright web agent if available
                if has_playwright:
                    try:
                        pw_index = 2 if has_github else 1
                        web_agent = AssistantAgent(
                            name=f"WebAgent_{request_count}",
                            description="An agent for web browsing and scraping using Playwright MCP.",
                            model_client=azure_model_client,
                            workbench=workbenches[pw_index],
                            model_client_stream=True,
                            max_tool_iterations=10,
                            system_message="""
                            You are a web browsing assistant using Playwright MCP tools.
                            Use tools to navigate, click, type, extract content, and answer questions from the live web.
                            Only browse when needed and cite the page URLs in your responses.
                            """,
                        )
                        participants.insert(2, web_agent)
                    except Exception as web_error:
                        print(f"⚠️  Playwright agent creation failed: {web_error}")
                        has_playwright = False

                # Create fresh team with unique agents
                team = MagenticOneGroupChat(
                    participants=participants,
                    model_client=azure_model_client,
                    termination_condition=termination,
                )
                
                # Use Console for clean output
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
    print("Starting MagenticOne Azure Infrastructure Agent Team...")
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
            # Create list of workbenches for multiple MCP servers with error handling
            workbenches = []
            for i, params in enumerate(server_params_list):
                try:
                    workbench = McpWorkbench(params)
                    workbenches.append(workbench)
                    args_str = " ".join(str(a) for a in getattr(params, "args", [])).lower()
                    if "@azure/mcp" in args_str:
                        server_type = "Azure"
                    elif "@azure-devops/mcp" in args_str or "azure-devops" in args_str:
                        server_type = "Azure DevOps"
                    elif "github-mcp" in args_str or "server-github" in args_str:
                        server_type = "GitHub"
                    elif "@playwright/mcp" in args_str:
                        server_type = "Playwright"
                    else:
                        server_type = "MCP"
                    print(f"✅ Created {server_type} MCP workbench")
                except Exception as e:
                    args_str = " ".join(str(a) for a in getattr(params, "args", [])).lower()
                    if "@azure/mcp" in args_str:
                        server_type = "Azure"
                    elif "@azure-devops/mcp" in args_str or "azure-devops" in args_str:
                        server_type = "Azure DevOps"
                    elif "github-mcp" in args_str or "server-github" in args_str:
                        server_type = "GitHub"
                    elif "@playwright/mcp" in args_str:
                        server_type = "Playwright"
                    else:
                        server_type = "MCP"
                    print(f"❌ Failed to create {server_type} MCP workbench: {e}")
                    if i == 0:  # Azure failed - this is critical
                        print("⚠️  Azure MCP workbench failed - continuing without MCP tools")
                        workbenches = None
                        break
                    else:  # GitHub failed - continue with Azure only
                        print("🔄 Continuing with Azure MCP only")
            
            if workbenches:
                print(f"✅ Successfully created {len(workbenches)} MCP workbench(es)")
        
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
