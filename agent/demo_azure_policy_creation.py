"""
Azure Policy Creation Workflow Demo
Demonstrates how to use AI agent to create Azure Policies in the Azure-Compliance repository
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../.env")

print("""
🏷️ AZURE POLICY CREATION WORKFLOW
=================================

## STEP 1: START THE AI AGENT
-----------------------------
cd z:\\infrastructure-agent\\agent
python main_azure_ai_dynamic.py

## STEP 2: PASTE THIS COMPLETE INSTRUCTION
------------------------------------------
Copy the entire instruction below into the agent:

-------BEGIN COPY-------
""")

# Read and display the policy request
with open("../azure-compliance-policy-request.md", "r") as f:
    content = f.read()
    print(content)

print("""
-------END COPY-------

## STEP 3: WHAT THE AGENT WILL DO AUTOMATICALLY
----------------------------------------------
The agent will:
✅ Connect to the Azure-Compliance repository
✅ Scan the repository structure and existing policies
✅ Analyze current tag governance patterns
✅ Identify the best location for the new policy
✅ Create the policy definition JSON file
✅ Create parameter files and assignment templates
✅ Update documentation and README files
✅ Create a new branch for the policy
✅ Create a pull request with all changes

## STEP 4: EXPECTED OUTPUT
--------------------------
The agent will create these files:

### Policy Definition:
📄 policies/tags/inherit-tag-from-rg/policy.json
📄 policies/tags/inherit-tag-from-rg/parameters.json

### Assignment Templates:
📄 assignments/tags/inherit-tag-from-rg-assignment.json
📄 assignments/tags/inherit-tag-from-rg-parameters.json

### Documentation:
📄 docs/policies/inherit-tag-from-resource-group.md
📄 README.md (updated with new policy)

### Deployment:
📄 deploy/policies/inherit-tag-policy.bicep
📄 deploy/policies/inherit-tag-policy.parameters.json

## STEP 5: FOLLOW-UP COMMANDS
-----------------------------
After the analysis, ask the agent:
- "Create the policy definition file with the JSON I provided"
- "Generate parameter files for common scenarios like 'Environment' and 'CostCenter' tags"
- "Create deployment templates for subscription-level assignment"
- "Update the repository documentation"
- "Create a pull request with title 'Add: Tag inheritance policy for resource groups'"

## STEP 6: VALIDATION
---------------------
The agent can also:
- Validate the JSON schema against Azure Policy standards
- Test the policy logic with sample scenarios
- Create remediation task templates
- Generate testing documentation

🎯 This workflow gives you a complete Azure Policy implementation!
""")

print(f"\n🔥 READY TO USE!")
print("=" * 50)
print("1. Start the agent: python main_azure_ai_dynamic.py")
print("2. Copy the instruction above (between -------BEGIN COPY------- and -------END COPY-------)")
print("3. Paste it into the agent conversation")
print("4. The agent will analyze the Azure-Compliance repo and create your tag inheritance policy!")
print("=" * 50)
