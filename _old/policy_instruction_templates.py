"""
AI Agent Instructions for Policy Changes
Best practices for getting optimal results
"""

# TEMPLATE FOR POLICY CHANGE INSTRUCTIONS
OPTIMAL_INSTRUCTION_FORMAT = """

🎯 POLICY CHANGE REQUEST TEMPLATE
================================

## 1. CONTEXT & SCOPE
Repository: [your-repo-name]
Policy Type: [security/access/deployment/compliance/etc.]
Impact Level: [low/medium/high]

## 2. SPECIFIC REQUIREMENTS
Policy Name: "[exact name]"
Objective: "[what this policy should achieve]"

Requirements:
- [Specific requirement 1]
- [Specific requirement 2] 
- [Specific requirement 3]

## 3. ANALYSIS INSTRUCTIONS
Please:
1. Scan the repository structure to understand current architecture
2. Search for existing policies, configurations, and related files
3. Identify patterns in current implementation
4. Suggest which files need modification
5. Recommend new files to create

## 4. IMPLEMENTATION PREFERENCES
File Types to Consider: [.json, .yaml, .md, .py, etc.]
Naming Conventions: [follow existing patterns]
Location Preferences: [suggest appropriate directories]

## 5. EXAMPLES OF WHAT TO LOOK FOR
Current Patterns: "[describe existing policy patterns if known]"
Similar Implementations: "[reference any similar policies]"
Integration Points: "[where this policy should integrate]"

"""

# EXAMPLE INSTRUCTION - SECURITY POLICY
EXAMPLE_SECURITY_POLICY = """

🔒 ADD SECURITY POLICY REQUEST
=============================

## Context & Scope
Repository: infrastructure-agent
Policy Type: Security & Access Control
Impact Level: Medium

## Specific Requirements
Policy Name: "Branch Protection and Code Review Policy"
Objective: Ensure all code changes go through proper review process

Requirements:
- Require pull request reviews before merging to main branches
- Require status checks to pass (CI/CD, security scans)
- Restrict direct pushes to main/master branches  
- Require up-to-date branches before merging
- Dismiss stale reviews when new commits are pushed

## Analysis Instructions
Please:
1. Scan for existing GitHub workflow files (.github/ directory)
2. Check for current branch protection settings
3. Look for existing CI/CD configurations
4. Identify security-related files or configurations
5. Suggest integration with existing development workflow

## Implementation Preferences
File Types: .json, .yaml, .md files
Naming Conventions: Follow GitHub standards
Location: .github/ directory structure

## Integration Points
- GitHub Actions workflows
- Repository settings documentation
- Developer contribution guidelines
- CI/CD pipeline configurations

"""

# EXAMPLE INSTRUCTION - DEPLOYMENT POLICY  
EXAMPLE_DEPLOYMENT_POLICY = """

🚀 ADD DEPLOYMENT POLICY REQUEST
===============================

## Context & Scope
Repository: infrastructure-agent
Policy Type: Deployment & Environment Management
Impact Level: High

## Specific Requirements
Policy Name: "Environment Promotion and Approval Policy"
Objective: Control deployments across dev/staging/production environments

Requirements:
- Require manual approval for production deployments
- Automatic deployment to dev environment on PR merge
- Staging deployment requires successful dev deployment
- Production deployment requires staging validation
- Rollback procedures and approval workflows

## Analysis Instructions
Please:
1. Scan for existing deployment configurations (deploy/ directory)
2. Check current CI/CD pipeline files
3. Look for environment-specific configurations
4. Identify Azure/cloud deployment patterns
5. Review existing approval mechanisms

## Implementation Preferences
File Types: .bicep, .yaml, .json, .md
Naming Conventions: environment-policy-[env].yaml
Location: deploy/ or .github/workflows/

## Integration Points
- Azure DevOps pipelines
- Bicep template deployment
- GitHub Actions workflows
- Environment-specific configurations

"""

print("📋 INSTRUCTION TEMPLATES CREATED")
print("=" * 40)

print("""
🎯 HOW TO USE THESE TEMPLATES:

1. **Copy the template** that matches your policy type
2. **Fill in the specific details** for your use case
3. **Provide to the AI agent** using this exact format
4. **The agent will:**
   ✅ Scan your repository structure
   ✅ Analyze existing patterns
   ✅ Suggest specific files to modify
   ✅ Recommend new files to create
   ✅ Provide implementation guidance

💡 **Pro Tips:**
- Be specific about requirements
- Mention existing patterns if you know them
- Include integration preferences
- Specify file types and locations
- Provide context about impact level
""")
