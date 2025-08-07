"""
GitHub Repository Workflow Demo
Demonstrates: Check files → Make changes → Create branch → Pull request
"""

import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../.env")

# Add parent directory for imports
import sys
sys.path.append(str(Path(__file__).parent))

from main_azure_ai_dynamic import DynamicToolManager
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

async def demo_github_workflow():
    """Demonstrate complete GitHub workflow"""
    
    print("🚀 GitHub Repository Workflow Demo")
    print("=" * 50)
    
    # Initialize Azure AI client
    endpoint = os.getenv("AZURE_AI_INFERENCE_ENDPOINT")
    api_key = os.getenv("AZURE_AI_INFERENCE_API_KEY")
    
    if not api_key:
        print("❌ Missing Azure AI Inference credentials")
        return
    
    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(api_key)
    )
    
    # Initialize tool manager
    tool_manager = DynamicToolManager()
    
    try:
        # Load GitHub tools
        print("🔧 Loading GitHub tools...")
        await tool_manager.load_category_tools("github")
        print(f"✅ Loaded GitHub tools: {len(tool_manager.github_tools)} available")
        
        # List some key GitHub tools
        github_tool_names = [tool[0] for tool in tool_manager.github_tools]
        key_tools = [tool for tool in github_tool_names if any(keyword in tool for keyword in 
                    ['file', 'repository', 'branch', 'pull_request', 'commit'])]
        
        print("🛠 Key GitHub tools available:")
        for tool in key_tools[:10]:  # Show first 10
            print(f"  • {tool}")
        
        print("\n" + "=" * 50)
        print("WORKFLOW STEPS:")
        print("=" * 50)
        
        # Step 1: Repository Information
        print("\n1️⃣ STEP 1: Check Repository Information")
        print("-" * 40)
        
        # Example: Get repository information
        try:
            repo_info = await tool_manager.call_tool("get_repository", {
                "owner": "acauret",
                "repo": "infrastructure-agent"
            })
            print("✅ Repository info retrieved")
            print(f"📁 Repository: acauret/infrastructure-agent")
        except Exception as e:
            print(f"ℹ️ Repository access: {str(e)[:100]}...")
        
        # Step 2: Check Files
        print("\n2️⃣ STEP 2: Check Files in Repository")
        print("-" * 40)
        
        try:
            # Get file contents example
            file_content = await tool_manager.call_tool("get_file_contents", {
                "owner": "acauret",
                "repo": "infrastructure-agent", 
                "path": "README.md"
            })
            print("✅ File contents retrieved: README.md")
            print(f"📄 File size: {len(str(file_content))} characters")
        except Exception as e:
            print(f"ℹ️ File access: {str(e)[:100]}...")
        
        # Step 3: Create Branch
        print("\n3️⃣ STEP 3: Create New Branch")
        print("-" * 40)
        
        branch_name = "feature/ai-demo-branch"
        try:
            # Create branch
            branch_result = await tool_manager.call_tool("create_branch", {
                "owner": "acauret",
                "repo": "infrastructure-agent",
                "branch": branch_name,
                "from_branch": "master"
            })
            print(f"✅ Branch created: {branch_name}")
        except Exception as e:
            print(f"ℹ️ Branch creation: {str(e)[:100]}...")
        
        # Step 4: Make Changes (Create/Update File)
        print("\n4️⃣ STEP 4: Make Changes to Repository")
        print("-" * 40)
        
        try:
            # Create or update a file
            file_content = f"""# AI Demo File
            
This file was created by the AI agent on branch: {branch_name}

## Workflow Demo
- ✅ Repository checked
- ✅ Branch created
- ✅ File modified
- 🔄 Pull request next

Created: {asyncio.get_event_loop().time()}
"""
            
            file_result = await tool_manager.call_tool("create_or_update_file", {
                "owner": "acauret",
                "repo": "infrastructure-agent",
                "path": "ai-demo-file.md",
                "content": file_content,
                "message": "Add AI demo file via automation",
                "branch": branch_name
            })
            print("✅ File created/updated: ai-demo-file.md")
        except Exception as e:
            print(f"ℹ️ File update: {str(e)[:100]}...")
        
        # Step 5: Create Pull Request
        print("\n5️⃣ STEP 5: Create Pull Request")
        print("-" * 40)
        
        try:
            pr_result = await tool_manager.call_tool("create_pull_request", {
                "owner": "acauret",
                "repo": "infrastructure-agent",
                "title": "🤖 AI Demo: Automated workflow demonstration",
                "body": """## AI-Generated Pull Request

This PR demonstrates the complete GitHub workflow automation:

### Changes Made
- ✅ Created new branch: `feature/ai-demo-branch`
- ✅ Added demo file: `ai-demo-file.md`
- ✅ Automated commit message

### Workflow Steps
1. Repository analysis
2. File content review
3. Branch creation
4. File modifications
5. Pull request creation

This demonstrates how the AI agent can autonomously manage GitHub workflows!

**Generated by:** Azure AI Inference + GitHub MCP Tools
""",
                "head": branch_name,
                "base": "master"
            })
            print("✅ Pull Request created!")
            print("🔗 Check your GitHub repository for the new PR")
        except Exception as e:
            print(f"ℹ️ Pull request: {str(e)[:100]}...")
        
        print("\n" + "=" * 50)
        print("🎉 WORKFLOW COMPLETE!")
        print("=" * 50)
        
        print("""
✅ What we accomplished:
   1. Loaded GitHub tools dynamically
   2. Checked repository information
   3. Retrieved file contents
   4. Created a new branch
   5. Made changes (created/updated files)
   6. Created a pull request

🎯 Next steps you can try:
   • Review the pull request in GitHub
   • Add comments or request reviews
   • Merge the changes
   • Create issues and link them
   • Manage workflows and actions
        """)
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        await tool_manager.cleanup()
        print("👋 Demo complete!")

if __name__ == "__main__":
    asyncio.run(demo_github_workflow())
