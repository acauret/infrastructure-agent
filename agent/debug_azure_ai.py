"""Debug version of the Azure AI dynamic agent to trace message issues"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from main_azure_ai_dynamic import (
    DynamicToolManager, convert_messages_to_azure_ai_format, 
    AZURE_API_KEY, INFERENCE_ENDPOINT, AZURE_OPENAI_MODEL
)
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential

async def debug_single_request():
    """Debug a single subscription request"""
    
    # Initialize Azure AI Inference client
    credential = AzureKeyCredential(AZURE_API_KEY)
    client = ChatCompletionsClient(
        endpoint=INFERENCE_ENDPOINT,
        credential=credential
    )

    # Initialize dynamic tool manager
    tool_manager = DynamicToolManager()
    await tool_manager.initialize_servers()
    
    # Load Azure tools
    await tool_manager.load_category_tools("azure")
    available_tools = tool_manager.get_available_tools()
    
    print(f"🔧 Loaded {len(available_tools)} tools")
    
    # Create a simple conversation
    system_prompt = "You are an Azure infrastructure expert assistant with access to Azure tools."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "list subscriptions"}
    ]
    
    print(f"📝 Original messages: {len(messages)}")
    for i, msg in enumerate(messages):
        print(f"  {i}: {msg['role']} - {msg['content'][:50]}...")
    
    # Convert to Azure AI format
    azure_messages = convert_messages_to_azure_ai_format(messages)
    
    print(f"🔄 Converted messages: {len(azure_messages)}")
    for i, msg in enumerate(azure_messages):
        print(f"  {i}: {type(msg).__name__}")
    
    try:
        print("\n🚀 Making Azure AI request...")
        response = client.complete(
            model=AZURE_OPENAI_MODEL,
            messages=azure_messages,
            tools=available_tools,
            stream=True,
        )
        
        print("Assistant: ", end="", flush=True)
        assistant_message = {"role": "assistant", "content": "", "tool_calls": []}
        
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta:
                delta = chunk.choices[0].delta
                
                # Handle content streaming
                if hasattr(delta, 'content') and delta.content:
                    print(delta.content, end="", flush=True)
                    assistant_message["content"] += delta.content
                
                # Handle tool call streaming
                if hasattr(delta, 'tool_calls') and delta.tool_calls:
                    print(f"\n🔧 Tool call detected in chunk")
        
        print("\n✅ Request completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
    finally:
        await tool_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(debug_single_request())
