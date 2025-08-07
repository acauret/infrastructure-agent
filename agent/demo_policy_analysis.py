"""
Repository Policy Analysis Agent
Demonstrates how to get the agent to scan and suggest policy changes
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

async def demonstrate_policy_analysis():
    """Show how to use the agent for repository policy analysis"""
    
    print("🔍 REPOSITORY POLICY ANALYSIS DEMO")
    print("=" * 50)
    
    # Example policy request using optimal format
    POLICY_REQUEST = """
🔒 ADD SECURITY POLICY REQUEST
=============================

## Context & Scope
Repository: infrastructure-agent
Policy Type: Security & Access Control  
Impact Level: Medium

## Specific Requirements
Policy Name: "Code Quality and Security Policy"
Objective: Ensure code quality, security scanning, and proper review processes

Requirements:
- Require pull request reviews before merging to main branches
- Run automated security scans on all commits
- Require code quality checks (linting, testing)
- Block merges if security vulnerabilities found
- Require signed commits for production releases

## Analysis Instructions
Please:
1. Scan the repository structure to understand current setup
2. Search for existing GitHub workflows, security configs, and policies
3. Identify current CI/CD patterns and integration points
4. Look for existing quality gates and security measures
5. Suggest which files need modification and what new files to create

## Implementation Preferences
File Types: .yaml, .json, .md files
Naming Conventions: Follow GitHub Actions standards
Location: .github/ directory structure
Integration: With existing development workflow

## Integration Points
- GitHub Actions workflows
- Branch protection rules
- Code scanning alerts
- Pull request templates
- Developer documentation
"""

    print("📋 EXAMPLE POLICY REQUEST:")
    print("-" * 30)
    print(POLICY_REQUEST)
    
    print("\n🤖 AI AGENT ANALYSIS COMMANDS:")
    print("=" * 50)
    
    # Commands the agent would execute
    analysis_commands = [
        "Search for all files in the .github directory to understand current GitHub setup",
        "List all YAML and JSON configuration files to identify existing policies",
        "Get contents of GitHub workflow files to understand current CI/CD",
        "Search for security-related configurations and scanning tools",
        "Analyze repository structure to understand project organization",
        "Check for existing branch protection documentation",
        "Look for pull request templates and contribution guidelines"
    ]
    
    for i, command in enumerate(analysis_commands, 1):
        print(f"{i:2}. {command}")
    
    print(f"\n🎯 EXPECTED AI RESPONSE FORMAT:")
    print("-" * 30)
    
    expected_response = """
## REPOSITORY ANALYSIS RESULTS

### Current Structure Analysis:
- Found .github/workflows/ with existing CI actions
- Located deploy/ directory with Bicep templates  
- Identified agent/ directory with Python modules
- Found existing documentation in README.md

### Existing Security Measures:
- GitHub Actions for basic CI/CD
- Environment variable management
- Azure resource deployment workflows

### RECOMMENDED CHANGES:

#### Files to Modify:
1. `.github/workflows/ci.yml` - Add security scanning steps
2. `README.md` - Add security policy documentation
3. `.github/PULL_REQUEST_TEMPLATE.md` - Add security checklist

#### Files to Create:
1. `.github/workflows/security-scan.yml` - Automated security scanning
2. `.github/SECURITY.md` - Security policy documentation
3. `.github/branch-protection-config.json` - Branch protection settings
4. `SECURITY_POLICY.md` - Detailed security requirements

#### Integration Strategy:
- Integrate with existing Azure CI/CD pipeline
- Add security gates to existing workflows
- Update documentation to reflect new policies
- Configure branch protection via GitHub API

### IMPLEMENTATION PRIORITY:
1. High: Security scanning workflow
2. Medium: Branch protection configuration  
3. Low: Documentation updates
"""

    print(expected_response)
    
    print(f"\n💡 BEST PRACTICES FOR POLICY INSTRUCTIONS:")
    print("=" * 50)
    
    best_practices = [
        "✅ Be specific about the policy objective and requirements",
        "✅ Mention repository context and current setup if known", 
        "✅ Specify file types, naming conventions, and locations",
        "✅ Include integration preferences with existing systems",
        "✅ Provide examples of similar policies if available",
        "✅ Indicate impact level and priority",
        "✅ Ask for analysis before implementation suggestions",
        "✅ Request file-by-file recommendations with rationale"
    ]
    
    for practice in best_practices:
        print(f"  {practice}")

if __name__ == "__main__":
    asyncio.run(demonstrate_policy_analysis())
