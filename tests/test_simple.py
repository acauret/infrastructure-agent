#!/usr/bin/env python3
"""Simple test to debug the issue"""

print("Starting test...")

try:
    print("Loading dotenv...")
    from dotenv import load_dotenv
    load_dotenv()
    print("Dotenv loaded")
    
    print("Importing GitHub MCP server...")
    from agent.github_mcp_server import GitHubMCPServer
    print("Import successful")
    
    print("Creating server instance...")
    server = GitHubMCPServer()
    print("Server created successfully")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
