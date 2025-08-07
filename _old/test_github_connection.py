"""
Quick GitHub Connection Test
Tests if GitHub MCP server can connect and list tools
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../.env")

# Add parent directory for imports
import sys
sys.path.append(str(Path(__file__).parent))

from github_mcp_server import GitHubMCPServer

async def test_github_connection():
    """Test GitHub MCP server connection"""
    
    print("🧪 Testing GitHub MCP Server Connection")
    print("=" * 40)
    
    # Check environment
    github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not github_token:
        print("❌ GITHUB_PERSONAL_ACCESS_TOKEN not found in environment")
        return False
    
    print(f"✅ GitHub token found: {github_token[:10]}...")
    
    # Initialize GitHub server
    github_server = GitHubMCPServer()
    
    try:
        print("🔄 Initializing GitHub MCP server...")
        await github_server.initialize()
        print("✅ GitHub MCP server initialized successfully")
        
        # List tools
        tools = github_server.list_tools()
        print(f"✅ GitHub tools available: {len(tools)}")
        
        # Show first 10 tools
        print("\n🛠 Available GitHub tools (first 10):")
        for i, (name, description) in enumerate(tools[:10]):
            print(f"  {i+1:2}. {name:30} - {description[:50]}...")
        
        if len(tools) > 10:
            print(f"  ... and {len(tools) - 10} more tools")
        
        print("\n✅ GitHub connection test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ GitHub connection test FAILED: {e}")
        return False
    
    finally:
        # Cleanup
        try:
            await github_server.close()
            print("🧹 Cleanup completed")
        except:
            pass

if __name__ == "__main__":
    result = asyncio.run(test_github_connection())
    
    if result:
        print("""
🎉 SUCCESS! GitHub tools are ready.

🚀 You can now run the main agent:
   cd z:\\infrastructure-agent\\agent
   python main_azure_ai_dynamic.py

💡 Try commands like:
   • "Show me my repositories"
   • "Check files in infrastructure-agent repo"
   • "Create a new branch called test-branch"
   • "Create a pull request"
        """)
    else:
        print("""
❌ GitHub connection failed. Please check:
   • GITHUB_PERSONAL_ACCESS_TOKEN is set correctly
   • Docker is running (required for GitHub MCP server)
   • Network connectivity to GitHub
        """)
