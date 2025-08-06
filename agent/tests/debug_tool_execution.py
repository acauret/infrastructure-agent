#!/usr/bin/env python3
"""
Debug what tool is being called and what result we get
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

async def debug_tool_execution():
    """Debug what happens when we call subscription tools"""
    print("🔬 Debugging Tool Execution...")
    
    try:
        from main_streaming_final import SimpleToolManager
        
        # Initialize tool manager
        tool_manager = SimpleToolManager()
        await tool_manager.initialize_servers()
        
        # Load Azure tools
        await tool_manager.ensure_azure_loaded()
        available_tools = tool_manager.get_available_tools()
        
        print(f"📦 Available tools: {len(available_tools)}")
        
        # Find subscription-related tools
        subscription_tools = []
        for tool in available_tools:
            if 'subscription' in tool.get('function', {}).get('name', '').lower():
                subscription_tools.append(tool['function']['name'])
        
        print(f"🔍 Subscription tools found: {subscription_tools}")
        
        # Try calling the subscription_list tool directly
        if subscription_tools:
            tool_name = subscription_tools[0]  # Use first subscription tool
            print(f"\n🔄 Testing direct call to: {tool_name}")
            
            try:
                # First, learn what commands are available
                print("📚 Learning available commands...")
                learn_result = await tool_manager.execute_tool(tool_name, {"learn": True})
                print(f"📖 Learn result: {learn_result[:1000]}...")
                
                # Try calling with the correct command format
                print(f"\n🔄 Testing with 'subscription_list' command...")
                result = await tool_manager.execute_tool(tool_name, {"command": "subscription_list"})
                print(f"✅ Subscription_list command result length: {len(result)}")
                print(f"📊 Subscription_list result: {result[:1000]}...")
                
            except Exception as e:
                print(f"❌ Tool call failed: {e}")
                # Try without parameters to see what happens
                try:
                    result = await tool_manager.execute_tool(tool_name, {})
                    print(f"📊 No-param result: {result[:500]}...")
                except Exception as e2:
                    print(f"❌ No-param call also failed: {e2}")
        
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
    print("🚀 Tool Execution Debug")
    print("=" * 40)
    
    success = await debug_tool_execution()
    
    print("\n" + "=" * 40)
    print(f"📋 Debug Result: {'PASS' if success else 'FAIL'}")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
