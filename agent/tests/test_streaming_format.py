#!/usr/bin/env python3
"""
Test Azure AI Inference streaming format to understand the structure
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

async def test_azure_ai_streaming_format():
    """Test Azure AI Inference streaming to understand the format"""
    print("🔬 Testing Azure AI Inference streaming format...")
    
    try:
        from azure.ai.inference import ChatCompletionsClient
        from azure.ai.inference.models import SystemMessage, UserMessage
        from azure.core.credentials import AzureKeyCredential
        
        # Setup client
        base_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        model = os.getenv("AZURE_OPENAI_MODEL", "gpt-4.1")
        api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
        
        # Convert endpoint format
        if "openai.azure.com" in base_endpoint:
            resource_name = base_endpoint.split("//")[1].split(".")[0]
            inference_endpoint = f"https://{resource_name}.cognitiveservices.azure.com/openai/deployments/{model}"
        else:
            inference_endpoint = base_endpoint
        
        credential = AzureKeyCredential(api_key)
        client = ChatCompletionsClient(
            endpoint=inference_endpoint,
            credential=credential
        )
        
        # Create a simple tool
        tools = [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "The location"}
                    },
                    "required": ["location"]
                }
            }
        }]
        
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            UserMessage(content="What's the weather in Paris? Use the get_weather tool.")
        ]
        
        print("🔄 Starting streaming...")
        response = client.complete(
            model=model,
            messages=messages,
            tools=tools,
            stream=True,
        )
        
        print("📡 Analyzing streaming chunks...")
        chunk_count = 0
        
        for chunk in response:
            chunk_count += 1
            print(f"\n--- Chunk {chunk_count} ---")
            print(f"Type: {type(chunk)}")
            
            if hasattr(chunk, 'choices') and chunk.choices:
                choice = chunk.choices[0]
                print(f"Choice type: {type(choice)}")
                
                if hasattr(choice, 'delta') and choice.delta:
                    delta = choice.delta
                    print(f"Delta type: {type(delta)}")
                    print(f"Delta attributes: {dir(delta)}")
                    
                    if hasattr(delta, 'content') and delta.content:
                        print(f"Content: {delta.content}")
                    
                    if hasattr(delta, 'tool_calls') and delta.tool_calls:
                        print(f"Tool calls: {len(delta.tool_calls)}")
                        for i, tool_call in enumerate(delta.tool_calls):
                            print(f"  Tool call {i}: {type(tool_call)}")
                            print(f"  Attributes: {dir(tool_call)}")
                            
                            # Check for different possible attributes
                            for attr in ['index', 'id', 'call_id', 'function', 'name', 'arguments']:
                                if hasattr(tool_call, attr):
                                    value = getattr(tool_call, attr)
                                    print(f"    {attr}: {value} ({type(value)})")
            
            # Stop after 10 chunks to avoid too much output
            if chunk_count >= 10:
                break
        
        print(f"\n✅ Analyzed {chunk_count} chunks")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Run the streaming format test"""
    print("🚀 Azure AI Inference Streaming Format Analysis")
    print("=" * 60)
    
    success = await test_azure_ai_streaming_format()
    
    print("\n" + "=" * 60)
    print(f"📋 Test Result: {'PASS' if success else 'FAIL'}")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
