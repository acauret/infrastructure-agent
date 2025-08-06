#!/usr/bin/env python3
"""
Quick test: Can Azure AI Inference client use MCP tools?
"""
import asyncio
import os
import sys
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

async def test_azure_ai_inference_tools():
    """Test if Azure AI Inference can use MCP tools"""
    print("🔬 Testing Azure AI Inference with MCP Tools")
    print("=" * 50)
    
    try:
        # Import Azure AI Inference
        from azure.ai.inference import ChatCompletionsClient
        from azure.ai.inference.models import SystemMessage, UserMessage
        from azure.core.credentials import AzureKeyCredential
        
        # Import our dynamic tool manager
        from main import DynamicToolManager
        
        print("✅ Imports successful")
        
        # Setup credentials
        base_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        model = os.getenv("AZURE_OPENAI_MODEL", "gpt-4.1")
        api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
        
        if not api_key:
            print("❌ API key not available")
            return False
        
        # Convert endpoint format
        if "openai.azure.com" in base_endpoint:
            resource_name = base_endpoint.split("//")[1].split(".")[0]
            inference_endpoint = f"https://{resource_name}.cognitiveservices.azure.com/openai/deployments/{model}"
        else:
            inference_endpoint = base_endpoint
        
        print(f"📍 Endpoint: {inference_endpoint}")
        print(f"🤖 Model: {model}")
        
        # Initialize tool manager
        tool_manager = DynamicToolManager()
        print("🔧 Initializing MCP servers...")
        await tool_manager.initialize_servers()
        
        print("📦 Loading Azure tools...")
        await tool_manager.load_category_tools("azure")
        available_tools = tool_manager.get_available_tools()
        print(f"✅ Loaded {len(available_tools)} tools")
        
        # Initialize Azure AI Inference client
        credential = AzureKeyCredential(api_key)
        client = ChatCompletionsClient(
            endpoint=inference_endpoint,
            credential=credential
        )
        print("✅ Azure AI Inference client initialized")
        
        # Test 1: Basic request without tools
        print("\n🧪 Test 1: Basic request (no tools)")
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            UserMessage(content="What is Azure?")
        ]
        
        response = client.complete(
            messages=messages,
            model=model,
            max_tokens=50
        )
        print("✅ Basic request works")
        
        # Test 2: Request with tools parameter
        print("\n🧪 Test 2: Request with tools parameter")
        messages = [
            SystemMessage(content="You are an Azure infrastructure assistant."),
            UserMessage(content="What Azure subscriptions do I have access to?")
        ]
        
        try:
            response = client.complete(
                messages=messages,
                model=model,
                tools=available_tools[:3],  # Use just 3 tools
                max_tokens=100
            )
            
            print("✅ Azure AI Inference supports tools parameter!")
            
            # Check if model wants to call tools
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                    print(f"🎯 Model wants to call {len(choice.message.tool_calls)} tools:")
                    for tool_call in choice.message.tool_calls:
                        print(f"  📞 {tool_call.function.name}")
                    tool_support = True
                else:
                    print("💬 Model responded without tool calls")
                    if hasattr(choice.message, 'content'):
                        print(f"📝 Response: {choice.message.content[:100]}...")
                    tool_support = True  # Tools parameter accepted, even if not used
            else:
                print("⚠ Unexpected response format")
                tool_support = False
                
        except Exception as tool_error:
            print(f"❌ Tools parameter failed: {tool_error}")
            tool_support = False
        
        # Cleanup
        await tool_manager.cleanup()
        
        # Summary
        print("\n" + "=" * 50)
        print("📋 Summary:")
        print(f"✅ Basic Azure AI Inference: WORKS")
        print(f"{'✅' if tool_support else '❌'} Tool calling support: {'WORKS' if tool_support else 'NOT SUPPORTED'}")
        
        if tool_support:
            print("\n🎉 Azure AI Inference CAN work with MCP servers!")
            print("💡 You can use it as an alternative to OpenAI client")
        else:
            print("\n⚠ Azure AI Inference works but does NOT support tool calling")
            print("💡 Stick with OpenAI client for MCP server integration")
        
        return tool_support
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_azure_ai_inference_tools())
    sys.exit(0 if result else 1)
