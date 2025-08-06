#!/usr/bin/env python3
"""Simple test to debug GitHub MCP connection"""

import asyncio
import logging
import os
from mcp.client.sse import sse_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.DEBUG)

async def test_connection():
    print("Testing GitHub MCP connection...")
    
    github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not github_token:
        print("No GitHub token found")
        return
    
    print(f"Token found: {github_token[:10]}...")
    
    url = "https://api.githubcopilot.com/mcp/"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Content-Type": "application/json"
    }
    
    print(f"Trying to connect to: {url}")
    
    try:
        async with sse_client(url, headers) as (read, write):
            print("Successfully connected to GitHub MCP")
            return True
    except Exception as e:
        print(f"Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())
