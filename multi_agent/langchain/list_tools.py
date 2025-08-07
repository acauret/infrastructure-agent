"""
List available Azure MCP tools to see what's actually provided
"""
import asyncio
import logging
import os
import sys

# Add paths for MCP server imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agent'))

from dotenv import load_dotenv
from azure_mcp_server import AzureMCPServer

# Load environment variables
load_dotenv()

async def list_available_tools():
    """List all available tools from Azure MCP"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    logger = logging.getLogger("MCP_Tools")
    
    try:
        logger.info("🔵 Initializing Azure MCP Server...")
        azure_server = AzureMCPServer()
        await azure_server.initialize()
        
        tools = azure_server.list_tools()
        logger.info(f"🔵 Found {len(tools)} tools")
        
        print(f"\n{'='*80}")
        print(f"📋 AVAILABLE AZURE MCP TOOLS ({len(tools)} total)")
        print(f"{'='*80}")
        
        for i, (name, description) in enumerate(tools, 1):
            print(f"{i:2d}. {name}")
            print(f"    📝 {description}")
            print()
        
        print(f"{'='*80}\n")
        
        await azure_server.close()
        
    except Exception as e:
        logger.error(f"❌ MCP Server failed: {e}")

if __name__ == "__main__":
    asyncio.run(list_available_tools())
