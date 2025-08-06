#!/usr/bin/env python3
"""
Azure AI Inference Dynamic Agent Runner

This script helps you run the Azure AI Inference dynamic conversation agent correctly.

Usage:
    python run_agent.py              # Interactive mode
    python run_agent.py --test       # Test mode (verify setup)
    python run_agent.py --help       # Show this help
"""

import sys
import os
import asyncio

def show_help():
    print(__doc__)
    print("Requirements:")
    print("  - AZURE_OPENAI_ENDPOINT environment variable")
    print("  - AZURE_OPENAI_API_KEY environment variable")
    print("  - Interactive terminal (for conversation mode)")
    print()
    print("Environment setup:")
    print("  Set-Variable AZURE_OPENAI_ENDPOINT 'https://your-resource.cognitiveservices.azure.com/openai/deployments/gpt-4o'")
    print("  Set-Variable AZURE_OPENAI_API_KEY 'your-api-key'")

async def main():
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h', 'help']:
            show_help()
            return
        elif sys.argv[1] == '--test':
            print("🧪 Running Azure AI Inference agent in test mode...")
        else:
            print(f"❌ Unknown argument: {sys.argv[1]}")
            show_help()
            return
    
    # Check if we're in an interactive environment
    if not sys.argv[1:] and not sys.stdin.isatty():
        print("⚠ Warning: Not running in an interactive terminal!")
        print("💡 This agent requires an interactive terminal for conversation.")
        print("📝 Try running from Command Prompt or PowerShell directly.")
        print("🧪 Use '--test' flag to verify setup without interaction.")
        return
    
    # Import and run the main agent
    try:
        # Add the current directory to Python path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        from main_azure_ai_dynamic import run
        await run()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure main_azure_ai_dynamic.py is in the same directory")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Check your environment variables and network connection")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
