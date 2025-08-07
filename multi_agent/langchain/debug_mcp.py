"""
Debug script to test MCP tools directly and see what they return
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

async def test_mcp_tools():
    """Test MCP tools directly to see what they return"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    logger = logging.getLogger("MCP_Debug")
    
    try:
        logger.info("🔵 Initializing Azure MCP Server...")
        azure_server = AzureMCPServer()
        await azure_server.initialize()
        
        tools = azure_server.list_tools()
        logger.info(f"🔵 Loaded {len(tools)} tools")
        
        # Test each tool and show results
        test_tools = [
            "get_subscription_details",
            "list_resource_groups", 
            "list_all_resources",
            "list_virtual_networks"
        ]
        
        for tool_name in test_tools:
            try:
                logger.info(f"🧪 Testing tool: {tool_name}")
                result = await azure_server.call_tool(tool_name, {})
                
                print(f"\n{'='*60}")
                print(f"🔧 TOOL: {tool_name}")
                print(f"📏 LENGTH: {len(str(result))} characters")
                print(f"📄 CONTENT:")
                print(f"{result}")
                print(f"{'='*60}\n")
                
            except Exception as e:
                logger.error(f"❌ Tool {tool_name} failed: {e}")
                print(f"\n❌ TOOL {tool_name} ERROR: {e}\n")
        
        await azure_server.close()
        
    except Exception as e:
        logger.error(f"❌ MCP Server failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())
