#!/usr/bin/env python3
"""
Test different Azure AI client approaches for chat completions
"""
import asyncio
import os
import sys
import time
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential

# Load environment variables
load_dotenv(dotenv_path="../../.env")

# Always import OpenAI client as baseline
from openai import AzureOpenAI
from azure.identity import get_bearer_token_provider

def check_azure_ai_libraries():
    """Check what Azure AI libraries are available"""
    print("🔍 Checking available Azure AI libraries...")
    
    available_libs = []
    
    # Check Azure AI Inference
    try:
        import azure.ai.inference
        available_libs.append("azure.ai.inference")
        print("✅ azure.ai.inference")
    except ImportError:
        print("❌ azure.ai.inference")
    
    # Check Azure Cognitive Services
    try:
        import azure.cognitiveservices
        available_libs.append("azure.cognitiveservices")
        print("✅ azure.cognitiveservices")
    except ImportError:
        print("❌ azure.cognitiveservices")
    
    # Check Azure AI Language
    try:
        import azure.ai.textanalytics
        available_libs.append("azure.ai.textanalytics")
        print("✅ azure.ai.textanalytics")
    except ImportError:
        print("❌ azure.ai.textanalytics")
    
    # Check Azure AI Form Recognizer
    try:
        import azure.ai.formrecognizer
        available_libs.append("azure.ai.formrecognizer")
        print("✅ azure.ai.formrecognizer")
    except ImportError:
        print("❌ azure.ai.formrecognizer")
    
    return available_libs

async def test_openai_azure_client():
    """Test the standard OpenAI Azure client"""
    print("\n🧪 Testing OpenAI Azure Client...")
    
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    model = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")
    
    if not endpoint:
        print("❌ AZURE_OPENAI_ENDPOINT not set")
        return False
    
    print(f"📍 Endpoint: {endpoint}")
    print(f"🤖 Model: {model}")
    
    try:
        # Initialize credentials
        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(
            credential, "https://cognitiveservices.azure.com/.default"
        )
        
        # Initialize client
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_version="2024-04-01-preview",
            azure_ad_token_provider=token_provider,
        )
        
        print("✅ Client initialized")
        
        # Test simple completion
        messages = [
            {"role": "system", "content": "You are a helpful Azure infrastructure assistant."},
            {"role": "user", "content": "What Azure services can help with infrastructure monitoring? Respond briefly."}
        ]
        
        print("🔄 Making API request...")
        start_time = time.time()
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=100,
            temperature=0.7
        )
        
        end_time = time.time()
        
        print(f"✅ Response received in {end_time - start_time:.2f}s")
        print(f"📝 Content: {response.choices[0].message.content[:200]}...")
        print(f"🎯 Usage: {response.usage.total_tokens} tokens")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

async def test_streaming_response():
    """Test streaming responses with OpenAI Azure client"""
    print("\n🌊 Testing Streaming Response...")
    
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    model = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")
    
    try:
        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(
            credential, "https://cognitiveservices.azure.com/.default"
        )
        
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_version="2024-04-01-preview",
            azure_ad_token_provider=token_provider,
        )
        
        messages = [
            {"role": "user", "content": "List 3 Azure monitoring services with brief descriptions."}
        ]
        
        print("🔄 Starting streaming request...")
        start_time = time.time()
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=150,
            stream=True,
            temperature=0.5
        )
        
        print("📡 Streaming content: ", end="", flush=True)
        content = ""
        
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                content_piece = chunk.choices[0].delta.content
                print(content_piece, end="", flush=True)
                content += content_piece
        
        end_time = time.time()
        print(f"\n✅ Streaming completed in {end_time - start_time:.2f}s")
        print(f"📊 Total content length: {len(content)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
        return False

async def test_with_azure_tools():
    """Test with our Azure MCP tools"""
    print("\n🛠 Testing with Azure MCP Tools...")
    
    try:
        # Import our dynamic tool manager
        from main import DynamicToolManager
        
        tool_manager = DynamicToolManager()
        
        # Initialize and load Azure tools
        print("🔧 Initializing tool manager...")
        await tool_manager.initialize_servers()
        await tool_manager.load_category_tools("azure")
        
        available_tools = tool_manager.get_available_tools()
        print(f"📦 Loaded {len(available_tools)} Azure tools")
        
        # Test with tools
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        model = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")
        
        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(
            credential, "https://cognitiveservices.azure.com/.default"
        )
        
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_version="2024-04-01-preview",
            azure_ad_token_provider=token_provider,
        )
        
        messages = [
            {"role": "user", "content": "What Azure subscriptions do I have access to?"}
        ]
        
        print("🔄 Making request with tools...")
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=available_tools[:5],  # Use first 5 tools to avoid token limit
            max_tokens=200
        )
        
        if response.choices[0].message.tool_calls:
            print(f"🎯 Model wants to call {len(response.choices[0].message.tool_calls)} tools")
            for tool_call in response.choices[0].message.tool_calls:
                print(f"  📞 {tool_call.function.name}")
        else:
            print("💬 Model responded without tool calls")
            print(f"📝 Response: {response.choices[0].message.content[:200]}...")
        
        await tool_manager.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Tool test failed: {e}")
        return False

async def test_azure_ai_inference_with_tools():
    """Test Azure AI Inference client with MCP tools"""
    print("\n🔬 Testing Azure AI Inference with MCP Tools...")
    
    try:
        # Import Azure AI Inference
        from azure.ai.inference import ChatCompletionsClient
        from azure.ai.inference.models import SystemMessage, UserMessage
        from azure.core.credentials import AzureKeyCredential
        
        # Import our dynamic tool manager
        from main import DynamicToolManager
        
        tool_manager = DynamicToolManager()
        
        # Initialize and load Azure tools
        print("🔧 Initializing tool manager...")
        await tool_manager.initialize_servers()
        await tool_manager.load_category_tools("azure")
        
        available_tools = tool_manager.get_available_tools()
        print(f"📦 Loaded {len(available_tools)} Azure tools")
        
        # Setup Azure AI Inference client
        base_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        model = os.getenv("AZURE_OPENAI_MODEL", "gpt-4.1")
        api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
        
        if not api_key:
            print("❌ API key not available for Azure AI Inference")
            return False
        
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
        
        messages = [
            SystemMessage(content="You are a helpful Azure infrastructure assistant."),
            UserMessage(content="What Azure subscriptions do I have access to?")
        ]
        
        print("🔄 Testing Azure AI Inference with tools...")
        
        # Check if Azure AI Inference supports tools parameter
        try:
            response = client.complete(
                messages=messages,
                model=model,
                tools=available_tools[:3],  # Use fewer tools to test
                max_tokens=200
            )
            
            print("✅ Azure AI Inference supports tool calling!")
            
            if hasattr(response, 'choices') and response.choices:
                if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
                    print(f"🎯 Model wants to call {len(response.choices[0].message.tool_calls)} tools")
                    for tool_call in response.choices[0].message.tool_calls:
                        print(f"  📞 {tool_call.function.name}")
                else:
                    print("💬 Model responded without tool calls")
                    if hasattr(response.choices[0].message, 'content'):
                        print(f"📝 Response: {response.choices[0].message.content[:200]}...")
            
            await tool_manager.cleanup()
            return True
            
        except Exception as tool_error:
            print(f"⚠ Azure AI Inference tools parameter failed: {tool_error}")
            
            # Try without tools parameter
            try:
                response = client.complete(
                    messages=messages,
                    model=model,
                    max_tokens=200
                )
                
                print("✅ Azure AI Inference works without tools parameter")
                print("❌ Tool calling not supported by Azure AI Inference client")
                
                await tool_manager.cleanup()
                return False
                
            except Exception as basic_error:
                print(f"❌ Azure AI Inference basic request also failed: {basic_error}")
                await tool_manager.cleanup()
                return False
        
    except ImportError as import_error:
        print(f"❌ Import failed: {import_error}")
        return False
    except Exception as e:
        print(f"❌ Azure AI Inference tool test failed: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

async def test_azure_ai_inference_streaming():
    """Test Azure AI Inference client with streaming"""
    print("\n🌊 Testing Azure AI Inference Streaming...")
    
    try:
        # Try to import AzureAIChatCompletionClient first, fallback to ChatCompletionsClient
        try:
            from azure.ai.inference import AzureAIChatCompletionClient
            use_chat_completion_client = True
        except ImportError:
            from azure.ai.inference import ChatCompletionsClient
            from azure.ai.inference.models import SystemMessage, UserMessage
            use_chat_completion_client = False
        
        from azure.core.credentials import AzureKeyCredential
        
        # Setup credentials and endpoint
        base_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        model = os.getenv("AZURE_OPENAI_MODEL", "gpt-4.1")
        api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
        
        if not api_key:
            print("❌ API key not available for Azure AI Inference")
            return False
        
        # Convert endpoint format
        if "openai.azure.com" in base_endpoint:
            resource_name = base_endpoint.split("//")[1].split(".")[0]
            inference_endpoint = f"https://{resource_name}.cognitiveservices.azure.com/openai/deployments/{model}"
        else:
            inference_endpoint = base_endpoint
        
        print(f"📍 Endpoint: {inference_endpoint}")
        print(f"🤖 Model: {model}")
        
        credential = AzureKeyCredential(api_key)
        
        if use_chat_completion_client:
            print("🔧 Using AzureAIChatCompletionClient")
            client = AzureAIChatCompletionClient(
                model=model,
                endpoint=inference_endpoint,
                credential=credential,
                model_info={
                    "json_output": False,
                    "function_calling": False,
                    "vision": False,
                    "family": model,
                    "structured_output": False,
                },
            )
            
            # Messages for AzureAIChatCompletionClient
            messages = [
                {"role": "system", "content": "You are a helpful Azure assistant."},
                {"role": "user", "content": "List 3 Azure monitoring services with brief descriptions. Be detailed."}
            ]
        else:
            print("🔧 Using ChatCompletionsClient")
            client = ChatCompletionsClient(
                endpoint=inference_endpoint,
                credential=credential
            )
            
            # Messages for ChatCompletionsClient
            messages = [
                SystemMessage(content="You are a helpful Azure assistant."),
                UserMessage(content="List 3 Azure monitoring services with brief descriptions. Be detailed.")
            ]
        
        # Test regular completion first
        print("🔄 Testing regular completion...")
        start_time = time.time()
        
        if use_chat_completion_client:
            response = await client.complete(
                messages=messages,
                max_tokens=300,
                temperature=0.7
            )
        else:
            response = client.complete(
                messages=messages,
                model=model,
                max_tokens=300,
                temperature=0.7
            )
        
        regular_time = time.time() - start_time
        print(f"✅ Regular completion: {regular_time:.2f}s")
        
        # Test streaming completion
        print("🔄 Testing streaming completion...")
        start_time = time.time()
        
        try:
            if use_chat_completion_client:
                stream_response = await client.complete(
                    messages=messages,
                    max_tokens=300,
                    temperature=0.7,
                    stream=True
                )
            else:
                stream_response = client.complete(
                    messages=messages,
                    model=model,
                    max_tokens=300,
                    temperature=0.7,
                    stream=True
                )
            
            print("📡 Streaming content: ", end="", flush=True)
            content = ""
            
            # Handle streaming response
            if hasattr(stream_response, '__aiter__'):
                # Async iterator
                async for chunk in stream_response:
                    if hasattr(chunk, 'choices') and chunk.choices:
                        if hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta:
                            if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                                content_piece = chunk.choices[0].delta.content
                                print(content_piece, end="", flush=True)
                                content += content_piece
            else:
                # Regular iterator
                for chunk in stream_response:
                    if hasattr(chunk, 'choices') and chunk.choices:
                        if hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta:
                            if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                                content_piece = chunk.choices[0].delta.content
                                print(content_piece, end="", flush=True)
                                content += content_piece
            
            stream_time = time.time() - start_time
            print(f"\n✅ Streaming completed: {stream_time:.2f}s")
            print(f"📊 Content length: {len(content)} characters")
            
            # Compare performance
            if stream_time < regular_time:
                speedup = regular_time / stream_time
                print(f"🏆 Streaming was {speedup:.1f}x faster!")
            else:
                slowdown = stream_time / regular_time
                print(f"⚠ Streaming was {slowdown:.1f}x slower")
            
            return True
            
        except Exception as stream_error:
            print(f"❌ Streaming failed: {stream_error}")
            print("✅ Regular completion works, but streaming not supported")
            return True  # Still consider this a partial success
        
    except ImportError as import_error:
        print(f"❌ Import failed: {import_error}")
        return False
    except Exception as e:
        print(f"❌ Azure AI Inference streaming test failed: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

async def performance_benchmark():
    """Run performance benchmarks"""
    print("\n⚡ Running Performance Benchmark...")
    
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    model = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")
    
    try:
        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(
            credential, "https://cognitiveservices.azure.com/.default"
        )
        
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_version="2024-04-01-preview",
            azure_ad_token_provider=token_provider,
        )
        
        test_cases = [
            {"name": "Short Query", "content": "What is Azure?", "max_tokens": 50},
            {"name": "Medium Query", "content": "Explain Azure networking services and their use cases.", "max_tokens": 200},
            {"name": "Long Query", "content": "Compare Azure compute services including VMs, App Service, Functions, and Kubernetes. Include pricing considerations.", "max_tokens": 500}
        ]
        
        for test_case in test_cases:
            print(f"\n📊 Testing: {test_case['name']}")
            
            messages = [{"role": "user", "content": test_case["content"]}]
            
            # Regular completion
            start_time = time.time()
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=test_case["max_tokens"]
            )
            regular_time = time.time() - start_time
            
            # Streaming completion
            start_time = time.time()
            stream_response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=test_case["max_tokens"],
                stream=True
            )
            
            # Consume stream
            for chunk in stream_response:
                if chunk.choices and chunk.choices[0].delta:
                    pass  # Just consume the stream
            
            stream_time = time.time() - start_time
            
            print(f"  ⚡ Regular: {regular_time:.2f}s")
            print(f"  🌊 Streaming: {stream_time:.2f}s")
            print(f"  📊 Tokens: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Azure AI Client Test Suite")
    print("=" * 60)
    
    # Check available libraries
    available_libs = check_azure_ai_libraries()
    print(f"\n📦 Found {len(available_libs)} Azure AI libraries")
    
    # Run tests
    results = {}
    
    # Test OpenAI Azure client
    results["openai_client"] = await test_openai_azure_client()
    
    # Test streaming
    results["streaming"] = await test_streaming_response()
    
    # Test with tools (OpenAI client)
    results["openai_tools"] = await test_with_azure_tools()
    
    # Test Azure AI Inference with tools
    results["azure_ai_tools"] = await test_azure_ai_inference_with_tools()
    
    # Performance benchmark
    results["performance"] = await performance_benchmark()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
