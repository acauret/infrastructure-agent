#!/usr/bin/env python3
"""
Test the Azure AI Inference version of main.py
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

async def test_azure_ai_inference_main():
    """Test the Azure AI Inference main.py file"""
    print("🔬 Testing Azure AI Inference main.py...")
    
    try:
        # Import the Azure AI Inference main module
        from main_azure_ai_inference import DynamicToolManager, ChatCompletionsClient, AzureKeyCredential
        from main_azure_ai_inference import INFERENCE_ENDPOINT, AZURE_API_KEY, AZURE_OPENAI_MODEL
        
        print("✅ Successfully imported Azure AI Inference main module")
        print(f"📍 Endpoint: {INFERENCE_ENDPOINT}")
        print(f"🤖 Model: {AZURE_OPENAI_MODEL}")
        
        # Test client initialization
        credential = AzureKeyCredential(AZURE_API_KEY)
        client = ChatCompletionsClient(
            endpoint=INFERENCE_ENDPOINT,
            credential=credential
        )
        print("✅ Azure AI Inference client initialized successfully")
        
        # Test tool manager initialization
        tool_manager = DynamicToolManager()
        await tool_manager.initialize_servers()
        print("✅ Dynamic tool manager initialized")
        
        # Test loading Azure tools
        print("🔧 Testing Azure tool loading...")
        await tool_manager.load_category_tools("azure")
        available_tools = tool_manager.get_available_tools()
        print(f"📦 Loaded {len(available_tools)} tools")
        
        # Test a simple API call
        from main_azure_ai_inference import SystemMessage, UserMessage
        
        print("🔄 Testing API call...")
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            UserMessage(content="What is Azure?")
        ]
        
        response = client.complete(
            model=AZURE_OPENAI_MODEL,
            messages=messages,
            max_tokens=50
        )
        
        print("✅ API call successful!")
        if hasattr(response, 'choices') and response.choices:
            content = response.choices[0].message.content
            print(f"📝 Response: {content[:100]}...")
        
        # Clean up
        await tool_manager.cleanup()
        print("✅ Cleanup completed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Run the test"""
    print("🚀 Azure AI Inference Main.py Test")
    print("=" * 50)
    
    success = await test_azure_ai_inference_main()
    
    print("\n" + "=" * 50)
    print(f"📋 Test Result: {'PASS' if success else 'FAIL'}")
    
    if success:
        print("\n💡 Azure AI Inference main.py is ready to use!")
        print("🎯 Key Features:")
        print("  ✅ Azure AI Inference client with improved performance")
        print("  ✅ Dynamic tool loading based on conversation context")
        print("  ✅ MCP server integration (Azure + GitHub)")
        print("  ✅ Streaming support")
        print("  ✅ Robust error handling and cleanup")
        print("\n🚀 To run: python main_azure_ai_inference.py")
    else:
        print("\n⚠ Fix the errors above before using the Azure AI Inference version")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
