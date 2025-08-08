import os
from typing import AsyncGenerator, Dict, List, Optional, Tuple
import asyncio
import uuid
from contextlib import AsyncExitStack
import json

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams

# Load .env if present at app root (compose mounts it next to docker-compose.yml)
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))

# Configuration flag
ENABLE_MCP_TOOLS = os.getenv("ENABLE_MCP_TOOLS", "true").lower() == "true"
ENABLE_AZURE_MCP = os.getenv("ENABLE_AZURE_MCP", "true").lower() == "true"
ENABLE_AZURE_DEVOPS_MCP = os.getenv("ENABLE_AZURE_DEVOPS_MCP", "true").lower() == "true"
ENABLE_GITHUB_MCP = os.getenv("ENABLE_GITHUB_MCP", "true").lower() == "true"
ENABLE_PLAYWRIGHT_MCP = os.getenv("ENABLE_PLAYWRIGHT_MCP", "true").lower() == "true"
USE_OFFICIAL_GITHUB_MCP = os.getenv("USE_OFFICIAL_GITHUB_MCP", "true").lower() == "true"


def create_mcp_server_params() -> List[StdioServerParams]:
    """Create MCP server parameters (Azure, Azure DevOps, GitHub, Playwright) using env vars."""
    server_params: List[StdioServerParams] = []

    if not ENABLE_MCP_TOOLS:
        print("🚫 MCP tools disabled via ENABLE_MCP_TOOLS=false")
        return server_params

    # Azure MCP server parameters
    try:
        if ENABLE_AZURE_MCP:
            print("🔄 Creating Azure MCP server params...")
            azure_server_params = StdioServerParams(
                command="npx",
                args=["-y", "@azure/mcp@latest", "server", "start"],
                env=os.environ.copy(),
                read_timeout_seconds=90,
            )
            server_params.append(azure_server_params)
            print("✅ Azure MCP server params created")
        else:
            print("⏭️  Skipping Azure MCP: disabled by ENABLE_AZURE_MCP=false")
    except Exception as e:
        print(f"❌ Azure MCP server params creation failed: {e}")

    # Azure DevOps MCP server parameters (requires ADO_ORG and PAT)
    try:
        ado_org = os.getenv("ADO_ORG")
        ado_pat = os.getenv("ADO_PAT") or os.getenv("AZURE_DEVOPS_EXT_PAT")
        if ENABLE_AZURE_DEVOPS_MCP and ado_org and ado_pat:
            print("🔄 Creating Azure DevOps MCP server params...")
            current_env = os.environ.copy()
            # Both env names are commonly used; set both for safety
            current_env["ADO_PAT"] = ado_pat
            current_env["AZURE_DEVOPS_EXT_PAT"] = ado_pat

            ado_server_params = StdioServerParams(
                command="npx",
                args=["-y", "@azure-devops/mcp", ado_org],
                env=current_env,
                read_timeout_seconds=45,
            )
            server_params.append(ado_server_params)
            print("✅ Azure DevOps MCP server params created")
        elif ENABLE_AZURE_DEVOPS_MCP and ado_org and not ado_pat:
            print("⏭️  Skipping Azure DevOps MCP: missing ADO_PAT/AZURE_DEVOPS_EXT_PAT")
        else:
            print("❌ ADO_ORG not set - skipping Azure DevOps MCP")
    except Exception as e:
        print(f"❌ Azure DevOps MCP server params creation failed: {e}")
        print("🔄 Continuing without Azure DevOps MCP server")

    # GitHub MCP server parameters (with environment variables)
    try:
        github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        if ENABLE_GITHUB_MCP and github_token:
            print("🔄 Creating GitHub MCP server params...")
            print(f"🔑 GitHub token found: {github_token[:8]}...")

            current_env = os.environ.copy()
            current_env["GITHUB_PERSONAL_ACCESS_TOKEN"] = github_token
            current_env["GITHUB_TOKEN"] = github_token
            current_env["GH_TOKEN"] = github_token

            if USE_OFFICIAL_GITHUB_MCP:
                # Prefer official MCP GitHub server binary
                github_server_params = StdioServerParams(
                    command="server-github",
                    args=[],
                    env=current_env,
                    read_timeout_seconds=45,
                )
            else:
                # Run custom server via node to avoid npx dynamic installs and ensure path
                github_server_params = StdioServerParams(
                    command="node",
                    args=[
                        "/usr/local/lib/node_modules/github-mcp-custom/bin/index.js",
                        "stdio",
                    ],
                    env=current_env,
                    read_timeout_seconds=45,
                )
            server_params.append(github_server_params)
            print("✅ GitHub MCP server params created (npx-based with token)")
        else:
            if not ENABLE_GITHUB_MCP:
                print("⏭️  Skipping GitHub MCP: disabled by ENABLE_GITHUB_MCP=false")
            else:
                print("❌ GITHUB_PERSONAL_ACCESS_TOKEN not set - skipping GitHub MCP")
    except Exception as e:
        print(f"❌ GitHub MCP server params creation failed: {e}")
        print("🔄 Continuing without GitHub MCP server")

    # Playwright MCP server (web browsing)
    try:
        if ENABLE_PLAYWRIGHT_MCP:
            print("🔄 Creating Playwright MCP server params...")
            pw_params = StdioServerParams(
                command="npx",
                args=["@playwright/mcp@latest", "--headless"],
                env=os.environ.copy(),
                read_timeout_seconds=45,
            )
            server_params.append(pw_params)
            print("✅ Playwright MCP server params created")
        else:
            print("⏭️  Skipping Playwright MCP: disabled by ENABLE_PLAYWRIGHT_MCP=false")
    except Exception as e:
        print(f"❌ Playwright MCP server params creation failed: {e}")

    return server_params


async def stream_task(prompt: str) -> AsyncGenerator[str, None]:
    """Run the MagenticOne team for a single prompt and stream updates as NDJSON events."""
    # Model config
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
    api_version = os.getenv("AZURE_API_VERSION", "2024-12-01-preview")
    model_name = os.getenv("AZURE_MODEL_NAME", "gpt-4.1")
    deployment = os.getenv("AZURE_DEPLOYMENT_NAME", model_name)

    if not azure_endpoint or not api_key:
        yield json.dumps({"type": "error", "text": "Missing AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_KEY"}) + "\n"
        return

    # Termination conditions
    termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(max_messages=30)

    # Create model client
    model_client = AzureOpenAIChatCompletionClient(
        azure_endpoint=azure_endpoint,
        api_key=api_key,
        api_version=api_version,
        azure_deployment=deployment,
        model=model_name,
    )

    # Ensure Azure CLI login for ADO server if credentials are present
    async def ensure_azure_cli_login() -> None:
        client_id = os.getenv("AZURE_CLIENT_ID")
        client_secret = os.getenv("AZURE_CLIENT_SECRET")
        tenant_id = os.getenv("AZURE_TENANT_ID")
        if not (client_id and client_secret and tenant_id):
            return
        try:
            show = await asyncio.create_subprocess_exec(
                "az", "account", "show",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await show.wait()
            if show.returncode == 0:
                return
        except Exception:
            pass
        try:
            login = await asyncio.create_subprocess_exec(
                "az", "login", "--service-principal",
                "-u", client_id, "-p", client_secret,
                "--tenant", tenant_id,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await login.wait()
        except Exception:
            # Best-effort
            pass

    await ensure_azure_cli_login()

    # Prepare MCP workbenches
    params_list = create_mcp_server_params()
    bench_indices: Dict[str, int] = {}
    workbenches: List[McpWorkbench] = []

    async with AsyncExitStack() as stack:
        # Create and enter workbenches
        for i, params in enumerate(params_list):
            try:
                wb = McpWorkbench(params)
                try:
                    await asyncio.wait_for(stack.enter_async_context(wb), timeout=10)
                except asyncio.TimeoutError:
                    raise RuntimeError("Workbench startup timed out")

                if hasattr(wb, "initialize"):
                    try:
                        await asyncio.wait_for(wb.initialize(), timeout=8)
                    except asyncio.TimeoutError:
                        raise RuntimeError("Workbench initialization timed out")

                # Retry tool listing with per-try timeout
                last_err: Optional[Exception] = None
                is_azure = any("@azure/mcp" in str(a).lower() for a in getattr(params, "args", []))
                attempts = 6 if is_azure else 4
                per_try_timeout = 45 if is_azure else 20
                for _ in range(attempts):
                    try:
                        await asyncio.wait_for(wb.list_tools(), timeout=per_try_timeout)
                        last_err = None
                        break
                    except Exception as e:
                        last_err = e
                        await asyncio.sleep(0.5)
                if last_err is not None:
                    raise RuntimeError(f"list_tools failed after retries: {last_err}")

                workbenches.append(wb)
                args_str = " ".join(str(a) for a in getattr(params, "args", [])).lower()
                if "@azure/mcp" in args_str:
                    bench_indices["azure"] = i
                    yield json.dumps({"type": "status", "text": "Azure MCP connected"}) + "\n"
                elif "@azure-devops/mcp" in args_str or "azure-devops" in args_str:
                    bench_indices["ado"] = i
                    yield json.dumps({"type": "status", "text": "Azure DevOps MCP connected"}) + "\n"
                elif "github-mcp" in args_str or "server-github" in args_str:
                    bench_indices["github"] = i
                    yield json.dumps({"type": "status", "text": "GitHub MCP connected"}) + "\n"
                elif "@playwright/mcp" in args_str:
                    bench_indices["playwright"] = i
                    yield json.dumps({"type": "status", "text": "Playwright MCP connected"}) + "\n"
            except Exception as e:
                yield json.dumps({"type": "status", "text": f"Failed to connect MCP server: {e}"}) + "\n"

        # Build participants
        participants: List[AssistantAgent | UserProxyAgent] = []
        req_id = uuid.uuid4().hex[:8]

        has_github = "github" in bench_indices
        has_playwright = "playwright" in bench_indices
        has_infracoder = bool(has_github)

        team_description = "AzureAgent: Handles Azure infrastructure queries and commands"
        if has_github:
            team_description += "\n                        GitHubAgent: Handles GitHub repository analysis"
        if has_infracoder:
            team_description += "\n                        InfraCoderAgent: Handles Terraform/Bicep coding tasks with branching and PRs"

        coordinator_agent = AssistantAgent(
            name=f"MagenticOneOrchestrator_{req_id}",
            description="Coordinates tasks between available agents.",
            model_client=model_client,
            system_message=f"""
                    You are a MagenticOne coordinator agent for Azure infrastructure and analysis.
                    Team members available:
                        {team_description}

                    Be concise. Immediately delegate the smallest actionable task to the correct agent and present results briefly.
                    For Azure requests like "list subscriptions", assign directly to AzureAgent with the precise action (e.g., "subscription_list").
                    {"For GitHub queries (repositories, issues, PRs), assign to GitHubAgent." if has_github else "If GitHub tools are unavailable, state that briefly."}

                    Only say "TERMINATE" when all tasks are done and you've provided a short final summary.
                    """,
        )
        participants.append(coordinator_agent)

        azure_agent = AssistantAgent(
            name=f"AzureAgent_{req_id}",
            description="Azure infrastructure analysis and management.",
            model_client=model_client,
            workbench=workbenches[bench_indices["azure"]] if "azure" in bench_indices else None,
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
        participants.append(azure_agent)

        if "ado" in bench_indices:
            participants.append(
                AssistantAgent(
                    name=f"AdoAgent_{req_id}",
                    description="Azure DevOps operations (Projects, Repos, PRs, Work Items, Builds, Releases).",
                    model_client=model_client,
                    workbench=workbenches[bench_indices["ado"]],
                    model_client_stream=True,
                    max_tool_iterations=10,
                    system_message="""
                            You are an Azure DevOps expert with access to live Azure DevOps MCP tools.
                            Always call the available tools for Projects, Repos, Pull Requests, Work Items, Builds, and Releases.
                            Return real data only; do not invent.
                            """,
                )
            )

        if "github" in bench_indices:
            participants.append(
                AssistantAgent(
                    name=f"GitHubAgent_{req_id}",
                    description="GitHub repository analysis and operations.",
                    model_client=model_client,
                    workbench=workbenches[bench_indices["github"]],
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
            )

        if "playwright" in bench_indices and "github" in bench_indices:
            participants.append(
                AssistantAgent(
                    name=f"InfraCoderAgent_{req_id}",
                    description="Terraform/Bicep coding tasks; browse AVM modules; PR workflow.",
                    model_client=model_client,
                    workbench=[
                        workbenches[bench_indices["github"]],
                        workbenches[bench_indices["playwright"]],
                    ],
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
            )

        if "playwright" in bench_indices:
            participants.append(
                AssistantAgent(
                    name=f"WebAgent_{req_id}",
                    description="Web browsing and scraping using Playwright MCP.",
                    model_client=model_client,
                    workbench=workbenches[bench_indices["playwright"]],
                    model_client_stream=True,
                    max_tool_iterations=10,
                    system_message="""
                            You are a web browsing assistant using Playwright MCP tools.
                            Use tools to navigate, click, type, extract content, and answer questions from the live web.
                            Only browse when needed and cite the page URLs in your responses.
                            """,
                )
            )

        participants.append(UserProxyAgent(name=f"HumanUser_{req_id}", description="Human user"))

        team = MagenticOneGroupChat(
            participants=participants,
            model_client=model_client,
            termination_condition=termination,
        )

        # Announce request
        yield json.dumps({"type": "request", "role": "user", "text": prompt}) + "\n"
        yield json.dumps({"type": "status", "text": "Starting..."}) + "\n"

        try:
            async for update in team.run_stream(task=prompt):
                try:
                    msg_type = getattr(update, "type", None) or type(update).__name__
                    src = getattr(update, "source", None) or "system"
                    content = getattr(update, "content", None)
                    if content is None:
                        content = str(update)
                    # Token stream
                    if ("Chunk" in msg_type) or msg_type.endswith("ChunkEvent"):
                        yield json.dumps({"type": "chunk", "agent": src, "text": str(content)}) + "\n"
                        continue
                    # Text message
                    if "TextMessage" in msg_type:
                        yield json.dumps({"type": "message", "agent": src, "text": str(content)}) + "\n"
                        continue
                    # Tool call request
                    if "ToolCallRequestEvent" in msg_type:
                        calls = getattr(update, "content", []) or []
                        serializable = []
                        for c in calls:
                            serializable.append({
                                "name": getattr(c, "name", None),
                                "arguments": getattr(c, "arguments", None),
                            })
                        yield json.dumps({"type": "tool_call", "agent": src, "calls": serializable}) + "\n"
                        continue
                    # Tool call execution result
                    if "ToolCallExecutionEvent" in msg_type:
                        results = getattr(update, "content", []) or []
                        serializable = []
                        for r in results:
                            name = getattr(r, "name", None)
                            out = getattr(r, "content", None)
                            out_str = str(out) if out is not None else ""
                            try:
                                parsed = json.loads(out_str)
                            except Exception:
                                parsed = out_str
                            serializable.append({"name": name, "output": parsed})
                        yield json.dumps({"type": "tool_result", "agent": src, "results": serializable}) + "\n"
                        continue
                    # Fallback event
                    yield json.dumps({"type": "event", "agent": src, "name": msg_type, "text": str(content)}) + "\n"
                except Exception as ie:
                    yield json.dumps({"type": "event", "agent": "system", "name": "error", "text": str(ie)}) + "\n"
        except Exception as e:
            yield json.dumps({"type": "error", "text": str(e)}) + "\n"

        if "ado" in bench_indices:
            participants.append(
                AssistantAgent(
                    name=f"AdoAgent_{req_id}",
                    description="Azure DevOps operations (Projects, Repos, PRs, Work Items, Builds, Releases).",
                    model_client=model_client,
                    workbench=workbenches[bench_indices["ado"]],
                    model_client_stream=True,
                    max_tool_iterations=10,
                    system_message="""
                            You are an Azure DevOps expert with access to live Azure DevOps MCP tools.
                            Always call the available tools for Projects, Repos, Pull Requests, Work Items, Builds, and Releases.
                            Return real data only; do not invent.
                            """,
                )
            )

        if "github" in bench_indices:
            participants.append(
                AssistantAgent(
                    name=f"GitHubAgent_{req_id}",
                    description="GitHub repository analysis and operations.",
                    model_client=model_client,
                    workbench=workbenches[bench_indices["github"]],
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
            )

        if "playwright" in bench_indices and "github" in bench_indices:
            participants.append(
                AssistantAgent(
                    name=f"InfraCoderAgent_{req_id}",
                    description="Terraform/Bicep coding tasks; browse AVM modules; PR workflow.",
                    model_client=model_client,
                    workbench=[
                        workbenches[bench_indices["github"]],
                        workbenches[bench_indices["playwright"]],
                    ],
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
            )

        if "playwright" in bench_indices:
            participants.append(
                AssistantAgent(
                    name=f"WebAgent_{req_id}",
                    description="Web browsing and scraping using Playwright MCP.",
                    model_client=model_client,
                    workbench=workbenches[bench_indices["playwright"]],
                    model_client_stream=True,
                    max_tool_iterations=10,
                    system_message="""
                            You are a web browsing assistant using Playwright MCP tools.
                            Use tools to navigate, click, type, extract content, and answer questions from the live web.
                            Only browse when needed and cite the page URLs in your responses.
                            """,
                )
            )

        participants.append(UserProxyAgent(name=f"HumanUser_{req_id}", description="Human user"))

        team = MagenticOneGroupChat(
            participants=participants,
            model_client=model_client,
            termination_condition=termination,
        )

        # Compact, markdown-friendly start
        yield f"### Request\n- User: {prompt}\n\n### Run\n"
        try:
            # Buffer token chunks to avoid one-token-per-line
            chunk_buffer = ""
            prev_was_chunk = False

            async for update in team.run_stream(task=prompt):
                try:
                    msg_type = getattr(update, "type", None) or type(update).__name__
                    src = getattr(update, "source", None) or "system"
                    content = getattr(update, "content", None)
                    if content is None:
                        content = str(update)
                    if not isinstance(content, str):
                        content = str(content)

                    # Chunk events → buffer
                    is_chunk = ("Chunk" in msg_type) or msg_type.endswith("ChunkEvent")
                    if is_chunk:
                        chunk_buffer += content
                        prev_was_chunk = True
                        continue

                    # Flush buffered chunks once when type switches
                    if prev_was_chunk and chunk_buffer:
                        yield chunk_buffer + "\n"
                        chunk_buffer = ""
                        prev_was_chunk = False

                    pretty = None
                    # Text messages → "- Agent: content" with indentation for multiline
                    if "TextMessage" in msg_type:
                        text = content.strip()
                        if "\n" in text:
                            first, *rest = text.split("\n")
                            body = first + "\n" + "\n".join(f"  {line}" for line in rest)
                        else:
                            body = text
                        pretty = f"- {src}: {body}\n"

                    # Tool call requests → compact, single-line summary per call
                    elif "ToolCallRequestEvent" in msg_type:
                        lines = []
                        calls = getattr(update, "content", []) or []
                        for c in calls:
                            name = getattr(c, "name", None) or "(unknown)"
                            args = getattr(c, "arguments", None)
                            args_str = str(args) if args is not None else "{}"
                            if len(args_str) > 200:
                                args_str = args_str[:200] + "…"
                            lines.append(f"- {src} → tool: {name} `{args_str}`")
                        pretty = ("\n".join(lines) + "\n") if lines else None

                    # Tool execution results → pretty JSON block, truncated
                    elif "ToolCallExecutionEvent" in msg_type:
                        blocks = []
                        results = getattr(update, "content", []) or []
                        for r in results:
                            name = getattr(r, "name", None) or "(unknown)"
                            out = getattr(r, "content", None)
                            out_str = str(out) if out is not None else ""
                            pretty_json = None
                            try:
                                loaded = json.loads(out_str)
                                pretty_json = json.dumps(loaded, indent=2)
                            except Exception:
                                pretty_json = out_str
                            if pretty_json and len(pretty_json) > 1500:
                                pretty_json = pretty_json[:1500] + "\n… (truncated)"
                            blocks.append(f"- {src} → result: {name}\n```json\n{pretty_json}\n```")
                        pretty = ("\n".join(blocks) + "\n") if blocks else None

                    if pretty is None:
                        pretty = f"- {src}: {content}\n"

                    yield pretty
                except Exception:
                    yield f"{str(update)}\n"
            if prev_was_chunk and chunk_buffer:
                yield chunk_buffer + "\n"
        except Exception as e:
            yield f"❌ Execution error: {e}\n"


async def check_mcp_servers() -> List[dict]:
    """Quick diagnostic: try to start each configured MCP workbench and return status list."""
    results: List[dict] = []
    params_list = create_mcp_server_params()
    async with AsyncExitStack() as stack:
        for params in params_list:
            args_list = getattr(params, "args", [])
            args_str = " ".join(str(a) for a in args_list).lower()
            is_azure = "@azure/mcp" in args_str

            entry = {
                "args": args_list,
                "status": "unknown",
                "error": None,
            }
            try:
                wb = McpWorkbench(params)
                # Allow slower startup/handshake for Azure server
                startup_timeout = 20 if is_azure else 10
                init_timeout = 15 if is_azure else 8
                try:
                    await asyncio.wait_for(stack.enter_async_context(wb), timeout=startup_timeout)
                except asyncio.TimeoutError:
                    raise RuntimeError("startup timeout")

                if hasattr(wb, "initialize"):
                    try:
                        await asyncio.wait_for(wb.initialize(), timeout=init_timeout)
                    except asyncio.TimeoutError:
                        raise RuntimeError("initialize timeout")

                # Retry list_tools with per-try timeout to accommodate first-run warmup
                attempts = 6 if is_azure else 3
                per_try_timeout = 45 if is_azure else 12
                last_err: Optional[Exception] = None
                for _ in range(attempts):
                    try:
                        await asyncio.wait_for(wb.list_tools(), timeout=per_try_timeout)
                        last_err = None
                        break
                    except Exception as e:
                        last_err = e
                        await asyncio.sleep(0.5)
                if last_err is not None:
                    raise RuntimeError(f"list_tools failed after retries: {last_err}")

                entry["status"] = "ok"
            except Exception as e:
                entry["status"] = "error"
                entry["error"] = str(e)
            results.append(entry)
    return results

