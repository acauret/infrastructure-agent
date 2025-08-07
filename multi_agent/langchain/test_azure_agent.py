"""
Simple test to check if the Azure agent can actually call tools and respond
"""
import asyncio
import logging
import os
import sys

# Add paths for MCP server imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agent'))

from dotenv import load_dotenv
from langchain_orchestrator import AzureLangChainAgent

# Load environment variables
load_dotenv()

async def test_azure_agent():
    """Test the Azure agent directly"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    logger = logging.getLogger("Test")
    
    try:
        endpoint = os.getenv("AZURE_AI_INFERENCE_ENDPOINT")
        api_key = os.getenv("AZURE_AI_INFERENCE_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
        
        logger.info("🧪 Testing Azure Agent directly...")
        
        # Create Azure agent
        azure_agent = AzureLangChainAgent(endpoint, api_key)
        await azure_agent.initialize()
        
        # Test with a simple request
        logger.info("📝 Testing simple subscription request...")
        result = await azure_agent.process("List Azure subscriptions")
        
        print(f"\n{'='*60}")
        print(f"🔧 AZURE AGENT RESPONSE:")
        print(f"📏 LENGTH: {len(str(result))} characters")
        print(f"📄 CONTENT:")
        print(f"{result}")
        print(f"{'='*60}\n")
        
        await azure_agent.shutdown()
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_azure_agent())
