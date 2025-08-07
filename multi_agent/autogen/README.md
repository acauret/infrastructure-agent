
# Azure Infrastructure Agent with AutoGen 0.7.2

This implementation uses AutoGen 0.7.2 with native MCP (Model Context Protocol) integration for Azure infrastructure management.

## ✅ **Working Configuration**

- **AutoGen**: 0.7.2
- **OpenAI**: 1.94.0 (compatible range: 1.40-1.95)
- **Azure MCP Server**: Latest via npm
- **GitHub MCP Server**: `github-mcp-custom`
- **Azure DevOps MCP Server**: `@azure-devops/mcp`
- **Playwright MCP Server**: `@playwright/mcp`
- **Python**: 3.11+

## 🚀 **Installation**

### 1. Install Node.js Dependencies
```bash
npm install -g @azure/mcp@latest github-mcp-custom @azure-devops/mcp @playwright/mcp
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the project root:

```env
# Azure Authentication
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
AZURE_SUBSCRIPTION_ID=your-subscription-id

# Azure OpenAI (for the AI model)
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_API_VERSION=2024-10-21

# Model Configuration
AZURE_MODEL_NAME=gpt-4.1
AZURE_DEPLOYMENT_NAME=gpt-4.1

# Optional
ENABLE_MCP_TOOLS=true
GITHUB_PERSONAL_ACCESS_TOKEN=your-github-token

# Azure DevOps (optional)
AZDO_ORG=your-organization-name   # e.g. contoso
# Optional: Personal Access Token for ADO (if required by your env)
AZURE_DEVOPS_EXT_PAT=your-ado-pat
```

## 🎯 **Usage**

```bash
python autogen_agent_v2.py
```

### Example Commands:
- `list subscriptions` - List Azure subscriptions
- `list vnets` - List virtual networks  
- `show resource groups` - List resource groups
- `list my github repos` - List GitHub repositories for the authenticated user
- `list ADO projects` - List Azure DevOps projects (requires AZDO_ORG)
- `browse https://example.com and summarize` - Use Playwright MCP to browse and summarize
- `quit` - Exit

## 🔧 **Features**

- ✅ **Real Azure Data**: Uses actual Azure MCP tools (not generic instructions)
- ✅ **Streaming Output**: Real-time agent responses
- ✅ **Native MCP Integration**: Uses AutoGen 0.7.2's `McpWorkbench` with Azure, GitHub, Azure DevOps, and Playwright servers
- ✅ **Error Handling**: Robust async error management
- ✅ **Clean Tables**: Formatted output for Azure resources

## 🐛 **Troubleshooting**

### Common Issues:

1. **Import Errors**: Ensure you're using the correct OpenAI version range (1.40-1.95)
2. **MCP Server Not Found**: Install the required MCP servers via npm (`@azure/mcp`, `github-mcp-custom`, `@azure-devops/mcp`, `@playwright/mcp`)
3. **Authentication Errors**: Check your Azure env vars and `GITHUB_PERSONAL_ACCESS_TOKEN`, `AZDO_ORG`/`AZURE_DEVOPS_EXT_PAT`
4. **Timeout/Shutdown Errors**: You may see benign anyio/MCP shutdown warnings on exit; they are suppressed in code and safe to ignore
5. **Windows Console Emoji**: If you see `UnicodeEncodeError` for emoji in console, we use plain text output to avoid cp1252 issues

### Version Compatibility:
- ❌ OpenAI 1.99+ - causes `typing.Union` errors
- ❌ OpenAI <1.40 - missing required features  
- ✅ OpenAI 1.40-1.95 - confirmed working range

## 📚 References

- Azure DevOps MCP Server: [microsoft/azure-devops-mcp](https://github.com/microsoft/azure-devops-mcp)
- Playwright MCP Server: [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp)
