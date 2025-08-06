#!/usr/bin/env python3
"""
Debug what network tools are available
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

async def debug_network_tools():
    """Debug what network-related tools are available"""
    print("🔬 Debugging Network Tools...")
    
    try:
        from main_streaming_final import SimpleToolManager
        
        # Initialize tool manager
        tool_manager = SimpleToolManager()
        await tool_manager.initialize_servers()
        
        # Load Azure tools
        await tool_manager.ensure_azure_loaded()
        available_tools = tool_manager.get_available_tools()
        
        print(f"📦 Available tools: {len(available_tools)}")
        
        # Find network-related tools
        network_tools = []
        for tool in available_tools:
            tool_name = tool.get('function', {}).get('name', '').lower()
            tool_desc = tool.get('function', {}).get('description', '').lower()
            
            if any(keyword in tool_name or keyword in tool_desc for keyword in 
                   ['network', 'vnet', 'subnet', 'virtual', 'vpc', 'resource']):
                network_tools.append({
                    'name': tool.get('function', {}).get('name', ''),
                    'description': tool.get('function', {}).get('description', '')[:200] + '...'
                })
        
        print(f"🌐 Network-related tools found: {len(network_tools)}")
        for tool in network_tools:
            print(f"  - {tool['name']}: {tool['description']}")
        
        # Also check for general Azure resource tools
        print(f"\n🔍 All available tool names:")
        for tool in available_tools:
            tool_name = tool.get('function', {}).get('name', '')
            print(f"  - {tool_name}")
        
        # Cleanup
        await tool_manager.cleanup()
        print("\n✅ Debug completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Run the debug"""
    print("🚀 Network Tools Debug")
    print("=" * 40)
    
    success = await debug_network_tools()
    
    print("\n" + "=" * 40)
    print(f"📋 Debug Result: {'PASS' if success else 'FAIL'}")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
