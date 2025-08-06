"""Simple interactive test for the Azure AI dynamic agent"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from main_azure_ai_dynamic import run

async def main():
    print("🧪 Testing Azure AI Dynamic Agent...")
    print("💡 This will test a single 'list subscriptions' command")
    print("📝 The agent should load Azure tools and execute the subscription command")
    print()
    
    # Mock input to test subscription listing
    original_input = input
    test_inputs = ["list subscriptions", "exit"]
    input_iter = iter(test_inputs)
    
    def mock_input(prompt):
        try:
            value = next(input_iter)
            print(f"{prompt}{value}")
            return value
        except StopIteration:
            return "exit"
    
    # Replace input function temporarily
    import builtins
    builtins.input = mock_input
    
    try:
        await run()
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        # Restore original input
        builtins.input = original_input

if __name__ == "__main__":
    asyncio.run(main())
