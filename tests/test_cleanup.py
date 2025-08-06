#!/usr/bin/env python3
"""
Quick test script to verify cleanup behavior
"""
import asyncio
import sys
import os

# Add the agent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import DynamicToolManager

async def test_cleanup():
    """Test the cleanup process"""
    print("🧪 Testing cleanup behavior...")
    
    # Initialize tool manager
    tool_manager = DynamicToolManager()
    
    try:
        # Initialize servers
        await tool_manager.initialize_servers()
        print("✓ Servers initialized")
        
        # Load Azure tools
        await tool_manager.load_category_tools("azure")
        print("✓ Azure tools loaded")
        
        # Test cleanup
        print("🧹 Testing cleanup...")
        await tool_manager.cleanup()
        print("✓ Cleanup completed successfully")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_cleanup())
    print("🎉 Cleanup test passed!")
