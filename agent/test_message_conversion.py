"""Test script to debug Azure AI message conversion"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from main_azure_ai_dynamic import convert_messages_to_azure_ai_format

def test_message_conversion():
    """Test various message scenarios"""
    
    # Test case 1: Simple conversation without tools
    print("🧪 Test 1: Simple conversation")
    messages1 = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "list subscriptions"},
        {"role": "assistant", "content": "I'll help you list Azure subscriptions."}
    ]
    
    try:
        converted1 = convert_messages_to_azure_ai_format(messages1)
        print(f"✅ Converted {len(messages1)} messages to {len(converted1)} Azure messages")
        for i, msg in enumerate(converted1):
            print(f"  {i}: {type(msg).__name__}")
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
    
    # Test case 2: Conversation with tool calls
    print("\n🧪 Test 2: Conversation with tool calls")
    messages2 = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "list subscriptions"},
        {"role": "assistant", "content": None, "tool_calls": [
            {"id": "call_123", "type": "function", "function": {"name": "subscription", "arguments": '{"command": "subscription_list"}'}}
        ]},
        {"role": "tool", "tool_call_id": "call_123", "name": "subscription", "content": "Subscription data here"},
        {"role": "assistant", "content": "Here are your subscriptions..."}
    ]
    
    try:
        converted2 = convert_messages_to_azure_ai_format(messages2)
        print(f"✅ Converted {len(messages2)} messages to {len(converted2)} Azure messages")
        for i, msg in enumerate(converted2):
            print(f"  {i}: {type(msg).__name__}")
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
    
    # Test case 3: Orphaned tool messages (should be filtered out)
    print("\n🧪 Test 3: Orphaned tool messages")
    messages3 = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "list subscriptions"},
        {"role": "tool", "tool_call_id": "orphan_123", "name": "subscription", "content": "Orphaned tool result"},
        {"role": "assistant", "content": "I'll help you list Azure subscriptions."}
    ]
    
    try:
        converted3 = convert_messages_to_azure_ai_format(messages3)
        print(f"✅ Converted {len(messages3)} messages to {len(converted3)} Azure messages")
        for i, msg in enumerate(converted3):
            print(f"  {i}: {type(msg).__name__}")
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")

if __name__ == "__main__":
    test_message_conversion()
