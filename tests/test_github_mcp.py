#!/usr/bin/env python3
"""Test script to test Docker-based GitHub MCP server"""

import asyncio
import logging
from agent.github_mcp_server import GitHubMCPServer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.DEBUG)

async def test_github_mcp():
    print("Testing GitHub MCP Server (Docker)...")
    try:
        print("Creating GitHub server instance...")
        github_server = GitHubMCPServer()
        print("Starting session...")
        
        # Add timeout
        async with asyncio.timeout(30):  # 30 second timeout
            async with github_server.create_session():
                print("Session created successfully!")
                tools = github_server.list_tools()
                print(f"Successfully loaded {len(tools)} GitHub MCP tools")
                for tool_name, tool_desc in tools[:5]:  # Show first 5 tools
                    short_desc = tool_desc.split('.')[0] if '.' in tool_desc else tool_desc[:60]
                    print(f"  • {tool_name}: {short_desc}")
                return True
    except asyncio.TimeoutError:
        print("GitHub MCP Server test timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"GitHub MCP Server failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await test_github_mcp()
    if success:
        print("GitHub MCP Server working correctly!")
    else:
        print("GitHub MCP Server has issues")

if __name__ == "__main__":
    asyncio.run(main())
