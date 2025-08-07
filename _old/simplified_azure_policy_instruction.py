"""
SIMPLIFIED AZURE POLICY INSTRUCTION
===================================
This version avoids the agent getting stuck in loops
"""

print("""
🎯 SIMPLE & EFFECTIVE INSTRUCTION FOR AZURE POLICY
=================================================

Copy this SHORTER instruction into the agent instead:

-------BEGIN COPY-------

Please help me create an Azure Policy for tag inheritance in my Azure-Compliance repository.

Repository: https://github.com/acauret/Azure-Compliance
Task: Create a new Azure Policy that inherits tags from resource groups to child resources

Steps needed:
1. First, show me the current structure of the Azure-Compliance repository
2. Then create a policy definition file using this JSON:

{
    "properties": {
        "displayName": "Inherit a tag from the resource group",
        "mode": "Indexed",
        "description": "Adds or replaces the specified tag and value from the parent resource group when any resource is created or updated.",
        "metadata": {
            "category": "Tags"
        },
        "parameters": {
            "tagName": {
                "type": "String",
                "metadata": {
                    "displayName": "Tag Name",
                    "description": "Name of the tag, such as 'environment'"
                }
            }
        },
        "policyRule": {
            "if": {
                "allOf": [{
                        "field": "[concat('tags[', parameters('tagName'), ']')]",
                        "notEquals": "[resourceGroup().tags[parameters('tagName')]]"
                    },
                    {
                        "value": "[resourceGroup().tags[parameters('tagName')]]",
                        "notEquals": ""
                    }
                ]
            },
            "then": {
                "effect": "modify",
                "details": {
                    "roleDefinitionIds": [
                        "/providers/microsoft.authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c"
                    ],
                    "operations": [{
                        "operation": "addOrReplace",
                        "field": "[concat('tags[', parameters('tagName'), ']')]",
                        "value": "[resourceGroup().tags[parameters('tagName')]]"
                    }]
                }
            }
        }
    }
}

3. Place the policy in the appropriate directory following the existing repository structure
4. Create a new branch called "feature/tag-inheritance-policy"
5. Create a pull request with the new policy

Please start by showing me the repository structure first.

-------END COPY-------

🔧 WHY THIS WORKS BETTER:
========================
✅ Much shorter and focused
✅ Clear step-by-step progression  
✅ Asks for repository structure first
✅ Doesn't overwhelm the agent with too many instructions
✅ Prevents the tool calling loop issue

🚨 RESTART THE AGENT:
===================
1. Type 'exit' to quit the current agent session
2. Restart: python main_azure_ai_dynamic.py
3. Paste the simplified instruction above
4. The agent will work much better with this focused approach!
""")

print("\n" + "="*60)
print("🔥 USE THE SIMPLIFIED VERSION ABOVE - IT PREVENTS LOOPS!")
print("="*60)
