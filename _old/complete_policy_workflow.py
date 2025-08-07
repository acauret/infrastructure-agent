"""
COMPLETE WORKFLOW: How to Use AI Agent for Policy Analysis
==========================================================

Step-by-step guide to get the agent to scan and suggest policy changes
"""

print("""
🚀 COMPLETE WORKFLOW: AI AGENT POLICY ANALYSIS
==============================================

## STEP 1: START THE AI AGENT
----------------------------
cd z:\\infrastructure-agent\\agent
python main_azure_ai_dynamic.py

## STEP 2: USE THE OPTIMAL INSTRUCTION FORMAT
--------------------------------------------
Copy and paste this EXACT text into the agent:

-------BEGIN COPY-------

🔒 SECURITY POLICY ANALYSIS & IMPLEMENTATION REQUEST
===================================================

## 1. REPOSITORY CONTEXT
Repository: infrastructure-agent
Owner: acauret
Current Branch: master
Policy Category: Security & Code Quality

## 2. POLICY SPECIFICATION  
Name: "Comprehensive Security and Code Quality Policy"
Objective: Implement automated security scanning, code quality checks, and mandatory review processes
Priority: High
Timeline: Implementation within 2 weeks

### Requirements:
- Mandatory pull request reviews for all branches targeting main/master
- Automated security vulnerability scanning on every commit and pull request  
- Code quality gates including linting, testing, and coverage requirements
- Dependency scanning for known vulnerabilities and license compliance
- Secret detection to prevent accidental credential commits
- Signed commits required for production releases

### Success Criteria:
- Zero unreviewed code reaches protected branches
- All security vulnerabilities detected and blocked before merge
- Maintain 85%+ code coverage across the project
- All dependencies continuously scanned for vulnerabilities
- No secrets or credentials accidentally committed

## 3. ANALYSIS REQUEST
Please perform this systematic analysis:

### Phase 1: Repository Structure Scan
1. Scan the entire repository structure, focusing on .github/ directory
2. List all existing workflow files, configuration files, and policy documents
3. Identify current security measures, CI/CD setup, and automation
4. Map existing GitHub Actions, Azure integrations, and deployment workflows
5. Find all security-related documentation and governance files

### Phase 2: Current State Analysis  
1. Search for existing security scanning tools or configurations
2. Identify current workflow naming conventions and organization patterns
3. Locate integration points with Azure services and GitHub features
4. Analyze current branch protection rules and review requirements
5. Check for existing quality gates, testing frameworks, and coverage tools

### Phase 3: Gap Analysis & Recommendations
1. Compare current security posture against the specified requirements
2. Identify missing security scanning components and tools needed
3. Find gaps in code review processes and quality enforcement
4. Assess current secret management and credential handling practices
5. Evaluate adequacy of current branch protection and access controls

## 4. DELIVERABLE REQUEST
Please provide a comprehensive response with:

### Analysis Report:
- Complete inventory of current security measures and configurations
- Detailed gap analysis comparing current state to requirements
- Risk assessment for each identified gap or missing component
- Integration recommendations that work with existing Azure workflows

### Implementation Plan:
- Specific GitHub workflow files to create or modify (with file names)
- Branch protection rules and repository settings to configure
- Security scanning tools and GitHub Actions to integrate
- Documentation files to create or update
- Configuration changes needed for existing systems

### Step-by-Step Implementation Guide:
1. Priority 1: Critical security scanning workflow implementation
2. Priority 2: Branch protection and review requirement configuration  
3. Priority 3: Code quality gates and testing automation
4. Priority 4: Documentation updates and developer guidelines
5. Priority 5: Validation testing and monitoring setup

## 5. IMPLEMENTATION CONSTRAINTS
File Types: .yml, .yaml, .json, .md files preferred
Locations: .github/workflows/, .github/, root directory structure
Naming Conventions: Follow GitHub Actions standards (security-*, quality-*, ci-*)
Integration Requirements: Must integrate with existing Azure deployments and services
Compatibility: GitHub Actions, Azure DevOps, existing Python/Node.js toolchain

## 6. SPECIFIC SEARCH INSTRUCTIONS
Search for files containing: workflow, security, deploy, ci, cd, test, action
Exclude from analysis: node_modules, .venv, __pycache__, .git directories
Focus on file patterns: .github/workflows/*.yml, *.bicep, requirements.txt, package.json
Check for integrations: Azure services, GitHub Apps, third-party actions, existing automation

-------END COPY-------

## STEP 3: WHAT THE AGENT WILL DO
---------------------------------
The agent will automatically:
✅ Load GitHub tools to scan your repository
✅ Analyze current file structure and configurations
✅ Search for existing policies and security measures  
✅ Identify gaps between current state and requirements
✅ Suggest specific files to modify with detailed changes
✅ Recommend new files to create with content outlines
✅ Provide step-by-step implementation instructions
✅ Include integration guidance for existing systems

## STEP 4: EXPECTED RESPONSE FORMAT
-----------------------------------
The agent will provide:

### 📊 ANALYSIS SECTION:
- Current repository structure overview
- Existing security measures inventory
- CI/CD and automation assessment
- Gap analysis with risk levels

### 📋 RECOMMENDATIONS SECTION:
- Files to modify (with specific changes)
- New files to create (with templates)
- Configuration updates needed
- Integration points to consider

### 🛠 IMPLEMENTATION SECTION:
- Prioritized step-by-step instructions
- Command sequences for each change
- Validation steps and testing procedures
- Rollback plans for safety

## STEP 5: FOLLOW-UP COMMANDS
-----------------------------
After the analysis, you can ask for:
- "Create the security scanning workflow file"
- "Generate the branch protection configuration"
- "Update the README with security policy documentation"
- "Create a pull request with these changes"

🎯 This approach gives you maximum AI agent performance for policy analysis and implementation!
""")

print("\n" + "="*60)
print("🔥 READY TO USE! Copy the instruction above and paste it into:")
print("   python main_azure_ai_dynamic.py")
print("="*60)
