#!/usr/bin/env python3
"""Minimal test to isolate MCP issue"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_minimal_mcp():
    print("Testing minimal MCP connection...")
    try:
        # Create server parameters
        server_params = StdioServerParameters(
            command="npx",
            args=["@azure/mcp@latest", "server", "start"],
        )
        
        # Start the stdio client
        async with stdio_client(server_params) as (read, write):
            print("Connected to stdio client")
            
            # Create session
            session = ClientSession(read, write)
            
            # Initialize session 
            async with session:
                await session.initialize()
                print("Session initialized successfully")
                
                # List tools
                tools_result = await session.list_tools()
                print(f"Found {len(tools_result.tools)} tools")
                
        print("Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_minimal_mcp())
