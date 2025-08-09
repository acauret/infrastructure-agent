import os
import shutil
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

# Simple session registry for streaming + human-in-the-loop
class _StreamContext:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.outgoing: asyncio.Queue[Optional[str]] = asyncio.Queue()
        self.input_q: asyncio.Queue[str] = asyncio.Queue()

    def emit(self, obj: Dict) -> None:
        # Always include session id in events
        payload = dict(obj)
        payload.setdefault("session", self.session_id)
        line = json.dumps(payload) + "\n"
        # Non-blocking put
        try:
            self.outgoing.put_nowait(line)
        except asyncio.QueueFull:
            # Best-effort; should not happen with default size
            pass

_SESSIONS: Dict[str, _StreamContext] = {}

async def submit_user_input(session_id: str, text: str) -> bool:
    ctx = _SESSIONS.get(session_id)
    if not ctx:
        return False
    await ctx.input_q.put(text)
    return True


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
                # Prefer Node entrypoint for official server; fallback to PATH binary
                entry = "/usr/local/lib/node_modules/@modelcontextprotocol/server-github/dist/index.js"
                if os.path.exists(entry):
                    github_server_params = StdioServerParams(
                        command="node",
                        args=[entry, "stdio"],
                        env=current_env,
                        read_timeout_seconds=45,
                    )
                else:
                    bin_path = shutil.which("server-github")
                    if not bin_path:
                        raise RuntimeError("server-github not found; ensure global npm install or set USE_OFFICIAL_GITHUB_MCP=false")
                    github_server_params = StdioServerParams(
                        command=bin_path,
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
            # Prefer globally installed CLI to avoid npx dynamic install at runtime
            # Try override, then common bin names, then direct node path fallback.
            pw_env_bin = os.getenv("PLAYWRIGHT_MCP_BIN")
            candidate_bins = [
                pw_env_bin,
                "/usr/local/bin/playwright-mcp",
                "/usr/local/bin/mcp-playwright",
                "playwright-mcp",
                "mcp-playwright",
            ]

            # Prefer node module entrypoint for stability; it's present when npm -g installed
            node_entry = "/usr/local/lib/node_modules/@playwright/mcp/dist/index.js"
            chosen_command = None
            chosen_args = ["--headless"]

            if os.path.exists(node_entry):
                chosen_command = "node"
                chosen_args = [node_entry, "--headless"]
            else:
                for cand in candidate_bins:
                    if not cand:
                        continue
                    # If absolute path, require it to exist; if bare, verify via PATH
                    if cand.startswith("/"):
                        if os.path.exists(cand):
                            chosen_command = cand
                            break
                    else:
                        found = shutil.which(cand)
                        if found:
                            chosen_command = found
                            break

            if chosen_command is None:
                print("⏭️  Skipping Playwright MCP: CLI not found; set PLAYWRIGHT_MCP_BIN to override")
            else:
                pw_params = StdioServerParams(
                    command=chosen_command,
                    args=chosen_args,
                    env=os.environ.copy(),
                    read_timeout_seconds=60,
                )
                server_params.append(pw_params)
                print(f"✅ Playwright MCP server params created (command: {chosen_command})")
        else:
            print("⏭️  Skipping Playwright MCP: disabled by ENABLE_PLAYWRIGHT_MCP=false")
    except Exception as e:
        print(f"❌ Playwright MCP server params creation failed: {e}")

    return server_params


async def stream_task(prompt: str) -> AsyncGenerator[str, None]:
    """Run the MagenticOne team for a single prompt and stream updates as NDJSON events with session support."""
    req_id = uuid.uuid4().hex[:8]
    ctx = _StreamContext(req_id)
    _SESSIONS[req_id] = ctx

    # Model config
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
    api_version = os.getenv("AZURE_API_VERSION", "2024-12-01-preview")
    model_name = os.getenv("AZURE_MODEL_NAME", "gpt-4.1")
    deployment = os.getenv("AZURE_DEPLOYMENT_NAME", model_name)

    if not azure_endpoint or not api_key:
        ctx.emit({"type": "error", "text": "Missing AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_KEY"})
        # Terminate stream early
        try:
            ctx.outgoing.put_nowait(None)
        except Exception:
            pass
    else:
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
                pass

    async def run_team_and_emit() -> None:
            await ensure_azure_cli_login()

            params_list = create_mcp_server_params()
            bench_indices: Dict[str, int] = {}
            workbenches: List[McpWorkbench] = []

            async with AsyncExitStack() as stack:
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
                            ctx.emit({"type": "status", "text": "Azure MCP connected"})
                        elif "@azure-devops/mcp" in args_str or "azure-devops" in args_str:
                            bench_indices["ado"] = i
                            ctx.emit({"type": "status", "text": "Azure DevOps MCP connected"})
                        elif "github-mcp" in args_str or "server-github" in args_str:
                            bench_indices["github"] = i
                            ctx.emit({"type": "status", "text": "GitHub MCP connected"})
                        elif "@playwright/mcp" in args_str:
                            bench_indices["playwright"] = i
                            ctx.emit({"type": "status", "text": "Playwright MCP connected"})
                    except Exception as e:
                        ctx.emit({"type": "status", "text": f"Failed to connect MCP server: {e}"})
                        continue

                participants: List[AssistantAgent | UserProxyAgent] = []

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
                            system_message="Always use the available ADO tools and return real data only.",
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
                            system_message="Use GitHub tools; do not invent data.",
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
                            system_message="Use Playwright to browse AVM docs; use GitHub for repo ops.",
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
                            system_message="Browse as needed and cite URLs.",
                        )
                    )

                # Interactive user proxy bridged to our session input queue
                async def input_bridge(prompt_text: str, cancellation_token) -> str:
                    try:
                        ctx.emit({"type": "input_request", "prompt": prompt_text})
                        text = await ctx.input_q.get()
                        return text
                    except Exception as e:
                        ctx.emit({"type": "error", "text": f"input error: {e}"})
                        return ""

                participants.append(
                    UserProxyAgent(
                        name=f"HumanUser_{req_id}",
                        description="Human user",
                        input_func=input_bridge,
                    )
                )

                try:
                    names = [getattr(p, "name", "?") for p in participants]
                    ctx.emit({"type": "status", "text": f"Participants: {', '.join(names)}"})
                except Exception:
                    pass

                team = MagenticOneGroupChat(
                    participants=participants,
                    model_client=model_client,
                    termination_condition=termination,
                )

                ctx.emit({"type": "request", "role": "user", "text": prompt})
                ctx.emit({"type": "status", "text": "Starting..."})

                try:
                    async for update in team.run_stream(task=prompt):
                        try:
                            msg_type = getattr(update, "type", None) or type(update).__name__
                            src = getattr(update, "source", None) or "system"
                            content = getattr(update, "content", None)
                            if content is None:
                                content = str(update)
                            if ("Chunk" in msg_type) or msg_type.endswith("ChunkEvent"):
                                ctx.emit({"type": "chunk", "agent": src, "text": str(content)})
                                continue
                            if "TextMessage" in msg_type:
                                ctx.emit({"type": "message", "agent": src, "text": str(content)})
                                continue
                            if "ToolCallRequestEvent" in msg_type:
                                calls = getattr(update, "content", []) or []
                                serializable = []
                                for c in calls:
                                    serializable.append({
                                        "name": getattr(c, "name", None),
                                        "arguments": getattr(c, "arguments", None),
                                    })
                                ctx.emit({"type": "tool_call", "agent": src, "calls": serializable})
                                continue
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
                                ctx.emit({"type": "tool_result", "agent": src, "results": serializable})
                                continue
                            ctx.emit({"type": "event", "agent": src, "name": msg_type, "text": str(content)})
                        except Exception as ie:
                            ctx.emit({"type": "event", "agent": "system", "name": "error", "text": str(ie)})
                except Exception as e:
                    ctx.emit({"type": "error", "text": str(e)})
            # Signal completion
            try:
                ctx.outgoing.put_nowait(None)
            except Exception:
                pass

        # Kick off team in background
    asyncio.create_task(run_team_and_emit())

    # Emit the session id first so the client can correlate
    ctx.emit({"type": "session", "id": req_id})
    # Now stream lines from the outgoing queue
    try:
        while True:
            line = await ctx.outgoing.get()
            if line is None:
                break
            yield line
    finally:
        _SESSIONS.pop(req_id, None)


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

