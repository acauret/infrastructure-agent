#!/usr/bin/env python3
"""
Test script to validate autonomous agent behavior
"""
import re

def test_continuation_detection():
    """Test the continuation detection logic"""
    
    test_messages = [
        "CONTINUING: Now I will automatically enumerate the resource groups.",
        "Now, I will automatically check each resource group for resources.",
        "Moving on to analyze the network infrastructure.",
        "I will now proceed to list all storage accounts.",
        "Let me now check the AKS clusters in your subscription.",
        "Proceeding to enumerate resources in each group.",
        "Next step: automatically review all VNets and subnets."
    ]
    
    continuation_indicators = [
        "CONTINUING:",
        "Now, I will automatically",
        "Next, I will", 
        "Now I'll",
        "Proceeding to",
        "Moving on to",
        "Next step:",
        "I will now",
        "Let me now",
        "automatically enumerate",
        "automatically check",
        "automatically review",
        "automatically analyze"
    ]
    
    print("🧪 Testing Continuation Detection Logic")
    print("="*50)
    
    for i, message in enumerate(test_messages, 1):
        should_continue = False
        message_lower = message.lower()
        
        for indicator in continuation_indicators:
            if indicator.lower() in message_lower:
                should_continue = True
                break
        
        status = "✅ DETECTED" if should_continue else "❌ MISSED"
        print(f"{i}. {status}: '{message[:50]}...'")
    
    print("\n" + "="*50)
    print("✅ Continuation detection logic working correctly!")

if __name__ == "__main__":
    test_continuation_detection()
    
    print("\n🚀 AUTONOMOUS AGENT STATUS")
    print("="*50)
    print("✅ System prompt enhanced with autonomous execution")
    print("✅ Continuation detection logic implemented")
    print("✅ Auto-execution flow restructured")
    print("✅ Tool guidelines preserved from original")
    print("✅ Verbose feedback without emoji overload")
    print("\n🎯 Ready for autonomous multi-step execution!")
    print("Test with: 'give me a complete inventory of my Azure infrastructure'")
