#!/usr/bin/env python3
"""
Test the final streaming Azure AI Inference version
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

async def test_final_streaming():
    """Test the final streaming implementation"""
    print("🔬 Testing Final Streaming Azure AI Inference...")
    
    try:
        from main_streaming_final import SimpleToolManager, handle_user_request
        from azure.ai.inference import ChatCompletionsClient
        from azure.core.credentials import AzureKeyCredential
        
        # Setup
        AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
        AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL", "gpt-4.1")
        AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
        
        def get_inference_endpoint(base_endpoint: str, model: str) -> str:
            if "openai.azure.com" in base_endpoint:
                resource_name = base_endpoint.split("//")[1].split(".")[0]
                return f"https://{resource_name}.cognitiveservices.azure.com/openai/deployments/{model}"
            return base_endpoint
        
        INFERENCE_ENDPOINT = get_inference_endpoint(AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_MODEL)
        
        # Initialize
        credential = AzureKeyCredential(AZURE_API_KEY)
        client = ChatCompletionsClient(endpoint=INFERENCE_ENDPOINT, credential=credential)
        tool_manager = SimpleToolManager()
        
        print("✅ Client initialized")
        
        # Initialize servers
        await tool_manager.initialize_servers()
        print("✅ Tool manager initialized")
        
        # Test with "list subscriptions"
        print("\n🔄 Testing 'list subscriptions'...")
        await handle_user_request(client, tool_manager, "list subscriptions")
        
        # Test with "what github repositories do I have?"
        print("\n🔄 Testing 'what github repositories do I have?'...")
        await handle_user_request(client, tool_manager, "what github repositories do I have?")
        
        # Cleanup
        await tool_manager.cleanup()
        print("\n✅ Test completed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Run the test"""
    print("🚀 Final Streaming Azure AI Inference Test")
    print("=" * 60)
    
    success = await test_final_streaming()
    
    print("\n" + "=" * 60)
    print(f"📋 Test Result: {'PASS' if success else 'FAIL'}")
    
    if success:
        print("\n💡 Ready to use! Run: python main_streaming_final.py")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
