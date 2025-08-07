"""
OPTIMAL AI AGENT INSTRUCTIONS FOR POLICY CHANGES
=================================================

Copy and customize this template for best results:
"""

OPTIMAL_POLICY_INSTRUCTION = """
🎯 POLICY ANALYSIS & IMPLEMENTATION REQUEST
==========================================

## 1. REPOSITORY CONTEXT
Repository: {your-repo-name}
Owner: {owner}
Current Branch: {branch-name}
Policy Category: [Security/Deployment/Compliance/Access/Quality]

## 2. POLICY SPECIFICATION
Name: "{exact-policy-name}"
Objective: {clear-one-sentence-goal}
Priority: [Critical/High/Medium/Low]
Timeline: {when-needed}

### Requirements:
- {specific-requirement-1}
- {specific-requirement-2}
- {specific-requirement-3}

### Success Criteria:
- {measurable-outcome-1}
- {measurable-outcome-2}

## 3. ANALYSIS REQUEST
Please perform this analysis in order:

### Phase 1: Repository Scan
1. Scan the entire repository structure
2. List all configuration files (.yaml, .json, .toml, .cfg)
3. Identify existing policies and security measures
4. Map current CI/CD and automation workflows
5. Find documentation and governance files

### Phase 2: Pattern Analysis  
1. Search for similar policy implementations
2. Identify existing naming conventions
3. Locate integration points and dependencies
4. Analyze current file organization patterns
5. Check for existing templates and standards

### Phase 3: Gap Analysis
1. Compare current state with requirements
2. Identify missing policy components
3. Find potential conflicts with existing policies
4. Assess integration complexity
5. Evaluate implementation risks

## 4. DELIVERABLE REQUEST
Please provide:

### Analysis Report:
- Current state summary
- Gap analysis findings  
- Risk assessment
- Integration recommendations

### Implementation Plan:
- Files to modify (with specific changes)
- New files to create (with content outline)
- Configuration updates needed
- Documentation requirements

### Step-by-Step Instructions:
- Prioritized implementation order
- Command sequences for each change
- Validation steps for each component
- Rollback procedures if needed

## 5. IMPLEMENTATION CONSTRAINTS
File Types: {preferred-file-types}
Locations: {preferred-directories}
Naming: {follow-existing-patterns}
Integration: {must-work-with-existing-systems}
Compatibility: {version-requirements}

## 6. SPECIFIC SEARCH INSTRUCTIONS
Look for files containing: {keywords-to-search}
Exclude directories: {dirs-to-ignore}
Focus on patterns: {specific-patterns}
Check integrations: {integration-points}

"""

# READY-TO-USE EXAMPLES
SECURITY_POLICY_EXAMPLE = """
🔒 SECURITY POLICY ANALYSIS & IMPLEMENTATION
===========================================

## 1. REPOSITORY CONTEXT
Repository: infrastructure-agent
Owner: acauret  
Current Branch: master
Policy Category: Security

## 2. POLICY SPECIFICATION
Name: "Comprehensive Security and Code Quality Policy"
Objective: Implement automated security scanning, code quality checks, and review requirements
Priority: High
Timeline: Next 2 weeks

### Requirements:
- Mandatory pull request reviews for all branches
- Automated security vulnerability scanning on every commit
- Code quality gates (linting, testing, coverage)
- Signed commits required for production releases
- Dependency scanning and license compliance
- Secret detection and prevention

### Success Criteria:
- Zero unreviewed code reaches main branches
- All security vulnerabilities detected before merge
- 90%+ code coverage maintained
- All dependencies scanned for vulnerabilities

## 3. ANALYSIS REQUEST
Please perform this analysis in order:

### Phase 1: Repository Scan
1. Scan the entire repository structure, especially .github/ directory
2. List all workflow files, configuration files, and policies
3. Identify existing security measures and CI/CD setup
4. Map current GitHub Actions and automation
5. Find security-related documentation

### Phase 2: Pattern Analysis
1. Search for existing security scanning tools or configurations
2. Identify current workflow naming and organization patterns
3. Locate integration points with Azure and GitHub services
4. Analyze current branch protection and review setup
5. Check for existing quality gates and testing frameworks

### Phase 3: Gap Analysis
1. Compare current security posture with requirements
2. Identify missing security scanning components
3. Find gaps in code review and quality processes
4. Assess current secret management practices
5. Evaluate branch protection adequacy

## 4. DELIVERABLE REQUEST
Please provide:

### Analysis Report:
- Current security measures inventory
- Security gap analysis
- Risk assessment for each gap
- Integration recommendations with existing Azure workflows

### Implementation Plan:
- GitHub workflow files to create/modify
- Branch protection rules to implement
- Security scanning tools to integrate
- Documentation updates needed

### Step-by-Step Instructions:
1. Security scanning workflow implementation
2. Branch protection configuration
3. Pull request template updates
4. Developer documentation updates
5. Testing and validation procedures

## 5. IMPLEMENTATION CONSTRAINTS
File Types: .yml, .yaml, .json, .md
Locations: .github/workflows/, .github/, root directory
Naming: security-*, quality-*, follow GitHub Actions naming
Integration: Must work with existing Azure deployments
Compatibility: GitHub Actions, Azure DevOps integration

## 6. SPECIFIC SEARCH INSTRUCTIONS
Look for files containing: workflow, security, deploy, ci, cd, test
Exclude directories: node_modules, .venv, __pycache__
Focus on patterns: .github/workflows/*.yml, *.bicep, requirements.txt
Check integrations: Azure services, GitHub Apps, third-party actions
"""

print("📋 OPTIMAL INSTRUCTION TEMPLATE CREATED!")
print("=" * 50)

print("""
🎯 HOW TO USE THIS FOR MAXIMUM EFFECTIVENESS:

1. **Copy the template above**
2. **Fill in your specific details** in the { } placeholders
3. **Paste it directly into the AI agent conversation**
4. **The agent will systematically:**
   ✅ Scan your entire repository
   ✅ Analyze existing patterns and configurations  
   ✅ Identify gaps and integration points
   ✅ Suggest specific file changes with rationale
   ✅ Provide step-by-step implementation
   ✅ Include validation and testing steps

💡 **Key Success Factors:**
- Be specific about requirements and success criteria
- Ask for phased analysis (scan → analyze → recommend)
- Request both analysis AND implementation guidance
- Specify file types, locations, and naming preferences
- Include integration constraints and compatibility needs

🚀 **Example Command to Start:**
"Please analyze my repository for security policy implementation using the structured approach above"
""")

print(f"\n🔥 READY-TO-USE SECURITY POLICY EXAMPLE:")
print("=" * 50) 
print("Copy this and paste it into the agent:")
print("-" * 30)
print(SECURITY_POLICY_EXAMPLE)
