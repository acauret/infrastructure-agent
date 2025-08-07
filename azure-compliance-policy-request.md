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

### Success Criteria:
- Valid Azure Policy JSON that passes schema validation
- Policy can be deployed and assigned to subscriptions/resource groups
- Policy correctly inherits tags from resource groups to resources
- Includes remediation capabilities for existing resources
- Follows repository structure and naming conventions

### Policy Definition Details:
```json
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
```

## 3. ANALYSIS REQUEST
Please perform this systematic analysis:

### Phase 1: Repository Structure Scan
1. Scan the Azure-Compliance repository structure to understand organization
2. List all existing Azure Policy files, templates, and configurations
3. Identify current policy naming conventions and folder structure
4. Map existing policy categories and deployment patterns
5. Find documentation, README files, and governance guidelines

### Phase 2: Current State Analysis
1. Search for existing tag-related policies or governance rules
2. Identify current Azure Policy definition patterns and templates
3. Locate policy assignment files and parameter configurations
4. Analyze existing deployment mechanisms (ARM, Bicep, etc.)
5. Check for existing remediation tasks and role assignments

### Phase 3: Gap Analysis & Integration Planning
1. Compare existing tag policies against the new inheritance requirement
2. Identify where the new policy fits in the current repository structure
3. Find integration points with existing policy sets and initiatives
4. Assess naming conventions and file organization patterns
5. Evaluate deployment and testing mechanisms

## 4. DELIVERABLE REQUEST
Please provide a comprehensive response with:

### Analysis Report:
- Complete inventory of current Azure Policy repository structure
- Analysis of existing tag governance and policy patterns
- Gap analysis for tag inheritance capabilities
- Integration recommendations with existing policy framework

### Implementation Plan:
- Specific directory structure for the new tag inheritance policy
- File names and locations following repository conventions
- Policy definition file with proper JSON formatting
- Parameter files for different environments or scenarios
- Assignment templates for subscription/resource group deployment
- Documentation updates needed

### Step-by-Step Implementation Guide:
1. Priority 1: Create policy definition file in appropriate directory
2. Priority 2: Create parameter files for common tag scenarios
3. Priority 3: Create policy assignment templates
4. Priority 4: Update documentation and README files
5. Priority 5: Create testing and validation procedures

## 5. IMPLEMENTATION CONSTRAINTS
File Types: .json, .bicep, .md files preferred
Locations: Follow existing Azure-Compliance repository structure
Naming Conventions: Follow Azure Policy naming standards and repository patterns
Integration Requirements: Must integrate with existing policy framework
Compatibility: Azure Resource Manager, Azure Policy service, existing governance

## 6. SPECIFIC SEARCH INSTRUCTIONS
Search for files containing: policy, tag, inherit, governance, assignment, initiative
Exclude from analysis: .git, node_modules, temp directories
Focus on file patterns: *.json (policy definitions), *.bicep, *.md, README files
Check for integrations: Existing policy sets, initiatives, assignment patterns, deployment templates

## 7. SPECIFIC ACTIONS TO PERFORM
After analysis, please:
1. Create the tag inheritance policy definition file
2. Create appropriate parameter files
3. Create assignment templates
4. Update repository documentation
5. Create a new branch for this policy addition
6. Create a pull request with the new policy implementation
