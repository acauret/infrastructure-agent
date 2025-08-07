"""
🏷️ AZURE POLICY CREATION - READY TO USE
========================================

COPY THIS COMPLETE INSTRUCTION AND PASTE INTO THE AI AGENT:
"""

print("""
🚀 QUICK START: Azure Policy Creation
====================================

## STEP 1: Start the AI Agent
cd z:\\infrastructure-agent\\agent
python main_azure_ai_dynamic.py

## STEP 2: Copy & Paste This Complete Instruction
-----------------------------------------------

🏷️ AZURE POLICY ANALYSIS & IMPLEMENTATION REQUEST
===================================================

## 1. REPOSITORY CONTEXT
Repository: Azure-Compliance
Owner: acauret
Repository URL: https://github.com/acauret/Azure-Compliance
Current Branch: main
Policy Category: Azure Policy & Governance

## 2. POLICY SPECIFICATION
Name: "Inherit Tag from Resource Group Policy"
Objective: Create an Azure Policy that automatically inherits tags from parent resource groups to child resources
Priority: High
Timeline: Implementation within 1 week

### Requirements:
- Create a new Azure Policy definition for tag inheritance
- Policy should inherit specified tags from resource group to resources
- Include proper policy metadata, parameters, and rule definitions
- Support modify effect with proper role definitions for remediation
- Follow Azure Policy JSON schema and best practices
- Include deployment templates and parameter files

### Policy Definition (use this exact JSON):
{
    "properties": {
        "displayName": "Inherit a tag from the resource group",
        "mode": "Indexed",
        "description": "Adds or replaces the specified tag and value from the parent resource group when any resource is created or updated. Existing resources can be remediated by triggering a remediation task.",
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

## 3. ANALYSIS REQUEST
Please perform this systematic analysis:

1. Scan the Azure-Compliance repository structure to understand organization
2. Analyze existing Azure Policy files and naming conventions
3. Identify where the new tag inheritance policy should be placed
4. Create the complete policy implementation with all required files
5. Create a new branch and pull request with the implementation

## 4. SPECIFIC ACTIONS TO PERFORM
After analysis, please:
1. Create the tag inheritance policy definition file using the JSON above
2. Create appropriate parameter files for common scenarios
3. Create assignment templates for deployment
4. Update repository documentation
5. Create a new branch called "feature/tag-inheritance-policy"
6. Create a pull request with title "Add: Tag inheritance policy for resource groups"

-----------------------------------------------

## STEP 3: What the Agent Will Do
✅ Connect to Azure-Compliance repository
✅ Scan repository structure and existing policies
✅ Create policy definition files
✅ Create deployment templates
✅ Update documentation
✅ Create branch and pull request

## STEP 4: Expected Files Created
- Policy definition JSON file
- Parameter files
- Assignment templates
- Documentation updates
- Deployment scripts

🎯 This will give you a complete Azure Policy implementation!
""")

print("\n" + "="*60)
print("🔥 READY! Copy the instruction above and paste it into the agent!")
print("="*60)
