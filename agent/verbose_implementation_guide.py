"""
PRACTICAL IMPLEMENTATION: Make Agent Verbose Like Copilot
========================================================
This file shows exactly how to modify your agent for detailed feedback
"""

# STEP 1: Enhanced System Prompt
VERBOSE_SYSTEM_PROMPT = '''You are an Azure infrastructure expert assistant with comprehensive GitHub and Azure tools.

## COMMUNICATION STYLE - BE EXTREMELY VERBOSE
Always provide detailed, step-by-step feedback for EVERY action:

🔍 **ANALYZING**: [Always explain what you're examining and why]
🎯 **OBJECTIVE**: [State the specific goal clearly]  
📋 **PLAN**: [Break down the steps you'll take]
🔧 **ACTION**: [Describe exactly what tool you're about to use]
⏳ **EXECUTING**: [Show what command/tool is running]
📊 **RESULT**: [Summarize what was found/accomplished]
💡 **INSIGHT**: [Explain what this means for the task]
🔄 **NEXT STEP**: [Explain what you'll do next]

## REQUIRED WORKFLOW FOR EVERY REQUEST
1. 🔍 **ANALYZING REQUEST**: Explain user's objective
2. 📋 **CREATING PLAN**: Break task into clear steps  
3. 🔧 **STEP-BY-STEP EXECUTION**: 
   - Before each tool: Explain WHY you're using it
   - During execution: Show it's running
   - After tool: Summarize findings and implications
4. 💡 **INSIGHTS**: Explain what you learned
5. 🔄 **NEXT ACTIONS**: Always state what comes next

## TOOL USAGE - ALWAYS EXPLAIN
Before using ANY tool:
- WHY this specific tool is needed
- WHAT you expect to find  
- HOW it helps the overall objective

After using ANY tool:
- WHAT was found/accomplished
- WHAT this means for the task
- WHAT you'll do with this information

## EXAMPLE VERBOSE FLOW
🔍 **ANALYZING REQUEST**: User wants to create an Azure Policy for tag inheritance
🎯 **OBJECTIVE**: Create policy definition files in Azure-Compliance repository
📋 **PLAN**: 
   Step 1: Examine repository structure
   Step 2: Analyze existing policy patterns
   Step 3: Create policy definition file
   Step 4: Create supporting files
   Step 5: Create branch and pull request

🔧 **STEP 1 - REPOSITORY ANALYSIS**
🔍 **EXAMINING**: Azure-Compliance repository structure
🎯 **PURPOSE**: Understanding current organization patterns
⏳ **USING TOOL**: get_file_contents on root directory
📊 **EXECUTING**: Scanning repository structure...
✅ **FOUND**: Repository has /policies, /assignments, /docs directories
💡 **INSIGHT**: Well-organized structure with clear separation of concerns
🔄 **NEXT**: Examining policies directory for existing tag policies

Continue this pattern for EVERY action.

Be conversational, educational, and ALWAYS explain your reasoning step-by-step.'''

print(f"""
🎯 STEP-BY-STEP IMPLEMENTATION GUIDE
===================================

## METHOD 1: Quick Update (Recommended)
--------------------------------------
1. Update the system prompt file to be more verbose:
""")

print("""
UPDATE THIS FILE: z:\\infrastructure-agent\\prompts\\system_prompt_azure_ai.txt

Replace the current content with the verbose system prompt above.
""")

print(f"""
## METHOD 2: Add Verbose Tool Wrapper
-----------------------------------
Add this to your DynamicToolManager class:
""")

verbose_tool_code = '''
async def call_tool_with_feedback(self, tool_name: str, arguments: Dict) -> str:
    """Enhanced tool calling with detailed step-by-step feedback"""
    
    # Pre-execution feedback
    print(f"\\n🔧 **TOOL CALL**: {tool_name}")
    print(f"📋 **PURPOSE**: {self._explain_tool_purpose(tool_name, arguments)}")
    print(f"📊 **PARAMETERS**: {json.dumps(arguments, indent=2)}")
    print(f"⏳ **EXECUTING**: Running {tool_name}...")
    
    try:
        # Call the original tool method
        if "azure" in self.active_categories and tool_name in [tool[0] for tool in self.azure_tools]:
            result = await self.azure_server.call_tool(tool_name, arguments)
        elif "github" in self.active_categories and tool_name in [tool[0] for tool in self.github_tools]:
            result = await self.github_server.call_tool(tool_name, arguments)
        else:
            raise Exception(f"Tool {tool_name} not found")
        
        # Post-execution feedback
        result_preview = result[:150] + "..." if len(result) > 150 else result
        print(f"✅ **SUCCESS**: {tool_name} completed successfully")
        print(f"📊 **RESULT SIZE**: {len(result)} characters")
        print(f"📄 **PREVIEW**: {result_preview}")
        print(f"💡 **ANALYSIS**: {self._analyze_result(tool_name, result)}")
        
        return result
        
    except Exception as e:
        print(f"❌ **ERROR**: {tool_name} failed")
        print(f"🔍 **DETAILS**: {str(e)}")
        print(f"🔄 **NEXT**: Will try alternative approach")
        raise

def _explain_tool_purpose(self, tool_name: str, args: Dict) -> str:
    """Explain why we're using this specific tool"""
    explanations = {
        "get_file_contents": f"Reading {args.get('path', 'file')} to understand its structure and content",
        "get_repository": f"Getting repository information for {args.get('repo', 'unknown')} to understand setup",
        "list_directory": f"Exploring {args.get('path', 'directory')} to see file organization",
        "create_branch": f"Creating branch '{args.get('branch', 'new-branch')}' to isolate our changes",
        "create_or_update_file": f"Creating/updating {args.get('path', 'file')} with new content",
        "create_pull_request": f"Opening PR to merge changes from {args.get('head', 'branch')} to {args.get('base', 'main')}",
        "search_code": f"Searching for '{args.get('q', 'code')}' to find existing implementations",
    }
    return explanations.get(tool_name, f"Using {tool_name} to accomplish the current step")

def _analyze_result(self, tool_name: str, result: str) -> str:
    """Provide intelligent analysis of tool results"""
    if tool_name == "get_file_contents":
        if "policy" in result.lower():
            return "Found policy-related content - will analyze structure and patterns"
        elif ".json" in result:
            return "Found JSON content - will examine for policy definitions"
        elif "readme" in tool_name.lower():
            return "Found documentation - will review for contribution guidelines"
        else:
            return "Retrieved file content - will analyze for relevant information"
    elif tool_name == "get_repository":
        return "Got repository metadata - will use this to understand project structure"
    elif tool_name == "list_directory":
        file_count = result.count("\\n") if result else 0
        return f"Found {file_count} items - will examine for relevant files and patterns"
    elif tool_name == "create_branch":
        return "Branch created successfully - ready to make changes in isolation"
    elif tool_name == "create_or_update_file":
        return "File operation completed - changes are now ready for review"
    elif tool_name == "create_pull_request":
        return "Pull request created - ready for review and collaboration"
    else:
        return "Operation completed successfully - proceeding with next step"
'''

print(verbose_tool_code)

print(f"""
## METHOD 3: Update the Main Conversation Loop
--------------------------------------------
Replace the call_tool calls with call_tool_with_feedback:

In the main conversation loop, change:
    content = await tool_manager.call_tool(function_name, function_args)

To:
    content = await tool_manager.call_tool_with_feedback(function_name, function_args)

## QUICK TEST
-----------
1. Update the system prompt file
2. Add the verbose tool wrapper to DynamicToolManager
3. Start the agent: python main_azure_ai_dynamic.py
4. Try: "Show me the structure of my Azure-Compliance repository"

The agent will now provide detailed step-by-step feedback like:

🔍 **ANALYZING REQUEST**: User wants to see Azure-Compliance repository structure
🎯 **OBJECTIVE**: Examine repository organization and file layout
📋 **PLAN**: Use GitHub tools to explore repository contents step-by-step

🔧 **TOOL CALL**: get_repository
📋 **PURPOSE**: Getting repository metadata to understand project setup
⏳ **EXECUTING**: Running get_repository...
✅ **SUCCESS**: Repository information retrieved
💡 **ANALYSIS**: Repository is active with recent commits, proceeding to examine structure

🔧 **TOOL CALL**: get_file_contents  
📋 **PURPOSE**: Reading root directory to see main organization
⏳ **EXECUTING**: Running get_file_contents...
✅ **SUCCESS**: Root directory contents retrieved
💡 **ANALYSIS**: Found organized structure with policies/, docs/, assignments/ directories

🎉 This makes the agent much more transparent and educational!
""")

print("\\n" + "="*60)
print("🔥 IMPLEMENT THESE CHANGES FOR VERBOSE AGENT!")
print("="*60)
