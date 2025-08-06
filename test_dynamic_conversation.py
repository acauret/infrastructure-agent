"""Test script for the dynamic Azure AI Inference main file"""
import asyncio
import sys
import os

# Add the agent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))

async def test_dynamic_conversation():
    """Test the dynamic conversation functionality"""
    print("🧪 Testing Azure AI Inference Dynamic Conversation Agent")
    
    try:
        # Import the main module
        from main_azure_ai_dynamic import run
        
        # Test the conversation system
        await run()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Dynamic Conversation Test...")
    success = asyncio.run(test_dynamic_conversation())
    
    if success:
        print("✅ Test completed successfully")
    else:
        print("❌ Test failed")
        sys.exit(1)
