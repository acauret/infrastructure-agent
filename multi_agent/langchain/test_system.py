"""
Quick test script for LangChain Multi-Agent System
"""
import asyncio
import os
import sys
sys.path.append(os.path.dirname(__file__))

from langchain_orchestrator import LangChainOrchestrator

async def test_system():
    print("🧪 Testing LangChain Multi-Agent System...")
    
    orchestrator = LangChainOrchestrator()
    
    try:
        await orchestrator.initialize()
        
        # Test orchestrator classification
        test_requests = [
            "What's my Azure subscription status?",
            "Show me GitHub repositories",
            "Analyze my complete infrastructure setup"
        ]
        
        for request in test_requests:
            print(f"\n🔍 Testing: {request}")
            response = await orchestrator.process_request(request)
            print(f"📝 Response: {response[:200]}...")
        
        print("\n✅ LangChain Multi-Agent System Test Complete!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        await orchestrator.shutdown()

if __name__ == "__main__":
    # Quick test with minimal output
    os.environ["LOG_LEVEL"] = "ERROR"
    asyncio.run(test_system())
