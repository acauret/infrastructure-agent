import asyncio
import json
import logging
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import (
    SystemMessage, UserMessage, AssistantMessage, ToolMessage,
    ChatCompletionsToolCall, FunctionCall
)
from azure.core.credentials import AzureKeyCredential
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv("../.env")

# Add the parent directory to Python path for imports
import sys
sys.path.append(str(Path(__file__).parent))

# Import from our modules
from azure_mcp_server import AzureMCPServer

async def test_tool_calling():
    """Test Azure AI tool calling with Azure subscription tool"""
    
    # Initialize Azure AI Inference client
    endpoint = os.getenv("AZURE_AI_INFERENCE_ENDPOINT", "https://axiomintelligence-resource.cognitiveservices.azure.com/openai/deployments/gpt-4.1")
    api_key = os.getenv("AZURE_AI_INFERENCE_API_KEY")
    
    if not api_key:
        print("❌ AZURE_AI_INFERENCE_API_KEY environment variable not set")
        return False
    
    print(f"🔗 Using endpoint: {endpoint}")
    
    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(api_key)
    )
    
    # Initialize Azure MCP Server
    azure_server = AzureMCPServer()
    
    try:
        # Start the server
        await azure_server.initialize()
        
        # Get available tools
        if not azure_server.tools:
            print("❌ No tools available")
            return False
        
        # Find subscription tool
        subscription_tool = None
        for tool in azure_server.tools:
            if tool.name == "subscription":
                subscription_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                }
                break
        
        if not subscription_tool:
            print("❌ Subscription tool not found")
            return False
        
        print("🔧 Testing tool call...")
        
        # Create messages
        messages = [
            SystemMessage(content="You are an Azure expert. Use tools to answer questions about Azure resources. For subscription information, use the command parameter with value 'subscription_list'."),
            UserMessage(content="What Azure subscriptions do I have access to? Use the subscription tool with command 'subscription_list'.")
        ]
        
        # Make the API call with tools
        response = client.complete(
            model="gpt-4.1",
            messages=messages,
            tools=[subscription_tool],
            temperature=0.1
        )
        
        print(f"Response finish reason: {response.choices[0].finish_reason}")
        
        # Check if it's a tool call
        if response.choices[0].finish_reason.value == "tool_calls":
            tool_calls = response.choices[0].message.tool_calls
            
            if tool_calls:
                print(f"✅ Tool call made: {tool_calls[0].function.name}")
                print(f"Arguments: {tool_calls[0].function.arguments}")
                
                # Parse the arguments
                try:
                    args = json.loads(tool_calls[0].function.arguments)
                    print(f"Parsed args: {args}")
                    
                    # Call the tool
                    tool_result = await azure_server.call_tool(tool_calls[0].function.name, args)
                    print(f"Tool result: {tool_result[:200]}...")
                    
                    # Create assistant message with tool calls
                    assistant_message = AssistantMessage(tool_calls=tool_calls)
                    
                    # Create tool response message
                    tool_message = ToolMessage(
                        content=tool_result,  # tool_result is already a string
                        tool_call_id=tool_calls[0].id
                    )
                    
                    # Get final response
                    final_messages = [
                        SystemMessage(content="You are an Azure expert. Use tools to answer questions about Azure resources."),
                        UserMessage(content="What Azure subscriptions do I have access to?"),
                        assistant_message,
                        tool_message
                    ]
                    
                    final_response = client.complete(
                        model="gpt-4.1",
                        messages=final_messages,
                        tools=[subscription_tool],
                        temperature=0.1
                    )
                    
                    print(f"Final response: {final_response.choices[0].message.content}")
                    print("✅ Complete tool call workflow successful!")
                    return True
                    
                except Exception as e:
                    print(f"❌ Error processing tool call: {e}")
                    return False
            else:
                print("❌ No tool calls in response")
                return False
        else:
            print(f"❌ Expected tool calls, got: {response.choices[0].finish_reason}")
            return False
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        # Clean up
        try:
            await azure_server.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_tool_calling())
