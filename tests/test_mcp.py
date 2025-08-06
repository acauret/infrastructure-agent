#!/usr/bin/env python3
"""Test script to isolate MCP server issues"""

import asyncio
import logging
from agent.azure_mcp_server import AzureMCPServer

logging.basicConfig(level=logging.INFO)

async def test_azure_mcp():
    print("Testing Azure MCP Server...")
    try:
        azure_server = AzureMCPServer()
        async with azure_server.create_session():
            tools = azure_server.list_tools()
            print(f"Successfully loaded {len(tools)} Azure MCP tools")
            return True
    except Exception as e:
        print(f"Azure MCP Server failed: {e}")
        return False

async def main():
    success = await test_azure_mcp()
    if success:
        print("Azure MCP Server working correctly!")
    else:
        print("Azure MCP Server has issues")

if __name__ == "__main__":
    asyncio.run(main())
