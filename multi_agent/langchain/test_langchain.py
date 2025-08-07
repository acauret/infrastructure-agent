"""
Test script to verify LangChain with Azure AI Inference integration
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

async def test_langchain_azure():
    """Test LangChain with Azure AI Inference"""
    try:
        from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
        from langchain_core.prompts import ChatPromptTemplate
        from azure.core.credentials import AzureKeyCredential
        
        print("✅ LangChain imports successful!")
        
        # Get configuration
        endpoint = os.getenv("AZURE_AI_INFERENCE_ENDPOINT")
        api_key = os.getenv("AZURE_AI_INFERENCE_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
        
        if not endpoint or not api_key:
            print("❌ Missing Azure AI configuration")
            return
        
        print(f"🔵 Using endpoint: {endpoint}")
        print(f"🔑 API key configured: {'Yes' if api_key else 'No'}")
        
        # Initialize LangChain Azure AI model
        llm = AzureAIChatCompletionsModel(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key),
            model="gpt-4",
            temperature=0.1,
        )
        
        print("✅ LangChain Azure AI model initialized!")
        
        # Create a simple prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant."),
            ("human", "{input}")
        ])
        
        print("✅ ChatPromptTemplate created!")
        
        # Create a chain
        chain = prompt | llm
        
        print("✅ LangChain chain created!")
        
        # Test the chain
        response = await chain.ainvoke({"input": "Hello! Can you confirm LangChain is working?"})
        
        print(f"✅ LangChain response: {response.content[:100]}...")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_langchain_azure())
