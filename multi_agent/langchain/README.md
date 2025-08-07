# Multi-Agent Infrastructure Management System

A sophisticated multi-agent architecture for Azure infrastructure and GitHub operations management using Azure AI Inference models.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION ENGINE                     │
│                   (Mistral-Large-2411)                     │
│  • Request classification                                   │
│  • Agent coordination                                      │
│  • Response synthesis                                      │
└─────────────────┬─────────────┬─────────────────────────────┘
                  │             │
         ┌────────┴────────┐   ┌┴─────────────────┐
         │  AZURE AGENT    │   │   GITHUB AGENT   │
         │    (GPT-4)      │   │ (mistral-small)  │
         │                 │   │                  │
         │ ┌─────────────┐ │   │ ┌──────────────┐ │
         │ │ Azure MCP   │ │   │ │ GitHub MCP   │ │
         │ │ Server      │ │   │ │ Server       │ │
         │ │ 15+ Tools   │ │   │ │ 8+ Tools     │ │
         │ └─────────────┘ │   │ └──────────────┘ │
         └─────────────────┘   └──────────────────┘
```

## 🤖 Specialized Agents

### 🔵 Azure Infrastructure Agent (GPT-4)
**Expertise:**
- Azure subscription and resource management
- Virtual networks, subnets, and security groups
- Resource group organization and governance
- Azure monitoring and cost optimization
- Infrastructure as Code (ARM, Bicep, Terraform)
- Security best practices and compliance

**MCP Tools:**
- `get_subscription_details` - Get Azure subscription information
- `list_resource_groups` - List all resource groups
- `list_all_resources` - Get all resources across subscription
- `list_virtual_networks` - Analyze network topology
- `get_resource_details` - Detailed resource information
- And more...

### 🐙 GitHub Agent (Mistral-Small)
**Expertise:**
- GitHub repository management and organization
- CI/CD pipelines with GitHub Actions
- Code review and collaboration workflows
- Branch strategies and release management
- Security scanning and vulnerability management
- GitHub Apps and integrations

**MCP Tools:**
- `list_repositories` - List user/organization repositories
- `get_repository` - Get repository details
- `list_commits` - Get recent commits
- `list_pull_requests` - Get pull request information
- `list_issues` - Get repository issues
- And more...

## 🧠 Orchestration Engine (Mistral-Large-2411)

The orchestrator uses the largest model for intelligent decision-making:

1. **Request Classification**: Analyzes user requests to determine which agent(s) should handle them
2. **Task Routing**: Routes requests to appropriate specialized agents
3. **Cross-Platform Coordination**: Coordinates multi-agent responses for complex requests
4. **Response Synthesis**: Combines responses from multiple agents into coherent answers

### Task Types:
- **AZURE_INFRASTRUCTURE**: Pure Azure operations
- **GITHUB_OPERATIONS**: Pure GitHub operations  
- **CROSS_PLATFORM**: Requires both Azure and GitHub coordination
- **GENERAL_INQUIRY**: General questions handled by orchestrator

## 🚀 Usage Examples

### Azure Infrastructure Analysis
```
You: analyze my Azure subscription in detail

🎯 Classified as: azure_infrastructure
🔵 Routing to Azure Infrastructure Agent
📊 SUBSCRIPTION DETAILS: [detailed subscription info]
📁 RESOURCE GROUPS: [resource group analysis]
🔧 ALL RESOURCES: [comprehensive resource listing]
🌐 VIRTUAL NETWORKS: [network topology analysis]
```

### GitHub Repository Management
```
You: list my GitHub repositories and recent activity

🎯 Classified as: github_operations
🐙 Routing to GitHub Agent
📊 REPOSITORIES: [repository listing with details]
📝 RECENT ACTIVITY: [commits, PRs, issues]
```

### Cross-Platform Operations
```
You: show me the infrastructure and code status for my projects

🎯 Classified as: cross_platform
🔀 Cross-platform request - coordinating agents
[Combined analysis from both Azure and GitHub agents]
```

## ⚙️ Configuration

### Environment Variables (.env)
```properties
# Azure AI Inference
AZURE_AI_INFERENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/openai/deployments/model-name
AZURE_AI_INFERENCE_API_KEY=your-api-key

# Azure Credentials
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# GitHub
GITHUB_PERSONAL_ACCESS_TOKEN=your-github-token

# Logging Control
LOG_LEVEL=WARNING  # DEBUG, INFO, WARNING, ERROR, CRITICAL, or NONE
```

## 🔧 Installation & Setup

1. **Install Dependencies:**
   ```bash
   cd multi_agent
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   Copy and configure the `.env` file with your credentials

3. **Run the System:**
   ```bash
   python main_multi_agent.py
   ```

## 📊 Model Selection Strategy

- **Orchestrator**: `Mistral-Large-2411` - Large model for complex decision-making and coordination
- **Azure Agent**: `gpt-4` - Advanced model for complex Azure infrastructure analysis
- **GitHub Agent**: `mistral-small` - Efficient model for GitHub operations

This approach optimizes cost and performance by using the right model size for each task complexity.

## 🎛️ Logging Control

Control verbosity through the `LOG_LEVEL` environment variable:
- **NONE**: Clean output, conversation only
- **WARNING**: Minimal logging (recommended)
- **INFO**: Detailed agent operations
- **DEBUG**: Full system debugging

## 🔮 Future Enhancements

1. **LangChain Integration**: Add LangChain for advanced agent orchestration
2. **Memory System**: Persistent conversation memory across sessions
3. **Tool Creation**: Dynamic tool creation and agent specialization
4. **Workflow Automation**: Automated multi-step infrastructure workflows
5. **Custom Agents**: User-defined specialized agents for specific domains

## 🔒 Security

- All credentials stored in environment variables
- MCP servers provide secure, sandboxed tool execution
- Agent communication through structured protocols
- No credential exposure in logs (with proper LOG_LEVEL settings)

---

**Ready to manage your infrastructure with AI agents!** 🚀
