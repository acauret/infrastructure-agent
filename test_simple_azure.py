#!/usr/bin/env python3
"""
Test the simplified Azure agent with basic functionality
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_azure_simple():
    """Test Azure agent with simple analysis"""
    try:
        from multi_agent.langchain_orchestrator import AzureLangChainAgent
        
        # Initialize agent
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_KEY")  # Fixed environment variable name
        
        if not endpoint or not api_key:
            print("❌ Missing Azure OpenAI credentials")
            return
            
        agent = AzureLangChainAgent(endpoint, api_key)
        await agent.initialize()
        
        print("🧪 Testing Azure agent with simple analysis...")
        
        # Test simple request
        response = await agent.process("Tell me about Azure infrastructure best practices")
        print(f"📏 LENGTH: {len(response)} characters")
        print(f"📝 RESPONSE: {response[:200]}...")
        
        # Test analysis request
        response2 = await agent.process("Analyze the current Azure subscription")
        print(f"📏 LENGTH: {len(response2)} characters") 
        print(f"📝 RESPONSE: {response2[:200]}...")
        
        await agent.shutdown()
        print("✅ Test completed")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_azure_simple())
