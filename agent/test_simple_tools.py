"""Simplified Azure AI agent focusing on tool calls"""
import asyncio
import json
import os
import sys

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage, ToolMessage
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))
from azure_mcp_server import AzureMCPServer

load_dotenv()

async def test_tool_execution():
    """Test tool execution with Azure AI Inference"""
    
    # Azure AI configuration
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")
    AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
    
    # Convert endpoint format
    def get_inference_endpoint(base_endpoint: str, model: str) -> str:
        if "openai.azure.com" in base_endpoint:
            resource_name = base_endpoint.split("//")[1].split(".")[0]
            return f"https://{resource_name}.cognitiveservices.azure.com/openai/deployments/{model}"
        return base_endpoint
    
    INFERENCE_ENDPOINT = get_inference_endpoint(AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_MODEL)
    
    # Initialize Azure AI client
    credential = AzureKeyCredential(AZURE_API_KEY)
    client = ChatCompletionsClient(endpoint=INFERENCE_ENDPOINT, credential=credential)
    
    # Initialize Azure MCP server
    azure_server = AzureMCPServer()
    await azure_server.initialize()
    azure_tools = azure_server.formatted_tools
    
    print(f"🔧 Loaded {len(azure_tools)} Azure tools")
    
    # Test conversation
    messages = [
        SystemMessage(content="You are an Azure infrastructure expert assistant with access to Azure tools. For subscription operations, use the subscription tool with the command parameter: {'command': 'subscription_list'}."),
        UserMessage(content="list my Azure subscriptions")
    ]
    
    try:
        print("\n🚀 Making initial request...")
        response = client.complete(
            model=AZURE_OPENAI_MODEL,
            messages=messages,
            tools=azure_tools,
        )
        
        print(f"Response finish reason: {response.choices[0].finish_reason}")
        
        if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
            print(f"🔧 Tool calls found: {len(response.choices[0].message.tool_calls)}")
            
            # Add the assistant message with tool calls
            messages.append(AssistantMessage(tool_calls=response.choices[0].message.tool_calls))
            
            # Process each tool call
            for tool_call in response.choices[0].message.tool_calls:
                print(f"🔧 Calling tool: {tool_call.function.name}")
                print(f"📝 Arguments: {tool_call.function.arguments}")
                
                try:
                    # Parse arguments
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Call the Azure tool
                    result = await azure_server.call_tool(tool_call.function.name, function_args)
                    print(f"✅ Tool result: {result[:200]}...")
                    
                    # Add tool result to messages
                    messages.append(ToolMessage(content=result, tool_call_id=tool_call.id))
                    
                except Exception as e:
                    print(f"❌ Tool call failed: {e}")
                    messages.append(ToolMessage(content=f"Error: {e}", tool_call_id=tool_call.id))
            
            # Get final response
            print("\n🚀 Getting final response...")
            final_response = client.complete(
                model=AZURE_OPENAI_MODEL,
                messages=messages,
                tools=azure_tools,
            )
            
            print(f"🎯 Final response: {final_response.choices[0].message.content}")
            
        else:
            print(f"💬 Direct response: {response.choices[0].message.content}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await azure_server.close()

if __name__ == "__main__":
    asyncio.run(test_tool_execution())
