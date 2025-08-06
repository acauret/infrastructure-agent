"""Simple test to isolate the Azure AI Inference issue"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

load_dotenv()

async def test_simple_azure_ai():
    """Test Azure AI Inference with a simple request"""
    
    # Get credentials
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")
    AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
    
    if not AZURE_OPENAI_ENDPOINT or not AZURE_API_KEY:
        print("❌ Missing Azure credentials")
        return
    
    # Convert endpoint format
    def get_inference_endpoint(base_endpoint: str, model: str) -> str:
        if "openai.azure.com" in base_endpoint:
            resource_name = base_endpoint.split("//")[1].split(".")[0]
            return f"https://{resource_name}.cognitiveservices.azure.com/openai/deployments/{model}"
        return base_endpoint
    
    INFERENCE_ENDPOINT = get_inference_endpoint(AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_MODEL)
    
    print(f"🔗 Using endpoint: {INFERENCE_ENDPOINT}")
    
    # Initialize client
    credential = AzureKeyCredential(AZURE_API_KEY)
    client = ChatCompletionsClient(
        endpoint=INFERENCE_ENDPOINT,
        credential=credential
    )
    
    # Simple test without tools
    print("🧪 Testing simple conversation...")
    messages = [
        SystemMessage(content="You are a helpful Azure assistant."),
        UserMessage(content="Hello, can you help me with Azure subscriptions?")
    ]
    
    try:
        response = client.complete(
            model=AZURE_OPENAI_MODEL,
            messages=messages,
            stream=True
        )
        
        print("Assistant: ", end="", flush=True)
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    print(delta.content, end="", flush=True)
        print()
        print("✅ Simple test successful!")
        
    except Exception as e:
        print(f"❌ Simple test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_simple_azure_ai())
    if success:
        print("✅ Azure AI Inference is working correctly")
    else:
        print("❌ Azure AI Inference test failed")
