#!/usr/bin/env python3
# chat_cli.py
import asyncio
import httpx
import sys
from datetime import datetime


async def chat_with_agent():
    # Use local URL
    agent_url = "http://localhost:8000"
    session_id = f"cli-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    print("Azure Infrastructure Agent CLI")
    print("=" * 50)
    print(f"Connecting to: {agent_url}")
    print("Type 'exit' to quit")
    print("=" * 50)

    # Test connection first
    try:
        async with httpx.AsyncClient() as client:
            health = await client.get(f"{agent_url}/health")
            health_data = health.json()
            print(f"\n✓ Connected to agent")
            print(f"  - Status: {health_data.get('status', 'unknown')}")
            print(f"  - MCP Available: {health_data.get('mcp_available', False)}")
            print(f"  - MCP Working: {health_data.get('mcp_working', False)}")
            print(f"  - GitHub: {health_data.get('github_configured', False)}")
    except Exception as e:
        print(f"\n✗ Failed to connect to agent at {agent_url}")
        print(f"  Error: {str(e)}")
        print("\nMake sure the agent is running:")
        print("  uvicorn agent.main:app --reload")
        return

    print("\n" + "=" * 50)
    print("\nReady! Try commands like:")
    print("  - List all of the resource groups in my subscription")
    print("  - List all of the storage accounts in my subscription")
    print("  - Get the available tables in my storage accounts")
    print("  - Show network topology")
    print("  - Analyze infrastructure")
    print("=" * 50)

    async with httpx.AsyncClient(timeout=60.0) as client:
        while True:
            try:
                user_input = input("\nYou: ")

                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("Goodbye!")
                    break

                print("\nAgent: Processing...")

                response = await client.post(
                    f"{agent_url}/chat",
                    json={"message": user_input, "session_id": session_id},
                )

                if response.status_code != 200:
                    print(f"Error: Server returned {response.status_code}")
                    print(response.text)
                    continue

                result = response.json()

                # Display the agent's formatted response
                print(f"\nAgent:\n{result['response']}")

                # Only show actions in debug mode or if there was an error
                if result.get("actions_taken"):
                    has_error = any(
                        action.get("result", {}).get("error")
                        for action in result["actions_taken"]
                        if isinstance(action.get("result"), dict)
                    )
                    if has_error or user_input.lower().startswith("debug"):
                        print("\n[Debug] Actions taken:")
                        for action in result["actions_taken"]:
                            action_name = action.get("action", "unknown")
                            result_data = action.get("result", {})
                            if isinstance(result_data, dict) and result_data.get(
                                "error"
                            ):
                                print(
                                    f"  - {action_name}: ❌ {result_data.get('error')}"
                                )
                            else:
                                print(f"  - {action_name}: ✓")

                if result.get("pr_url"):
                    print(f"\n✅ Pull Request: {result['pr_url']}")

            except httpx.ReadTimeout:
                print(
                    "\n⏱️ Request timed out. The agent might be processing a large request."
                )
                print("   Try again or use a simpler query.")
            except httpx.ConnectError:
                print("\n✗ Lost connection to agent. Make sure it's still running.")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")


if __name__ == "__main__":
    # For Windows color support
    if sys.platform == "win32":
        import os

        os.system("color")

    try:
        asyncio.run(chat_with_agent())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
