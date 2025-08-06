# Azure AI Inference Dynamic Agent - Troubleshooting

## ❌ Issue: "EOF when reading a line" Error

### Problem Description
The error "EOF when reading a line" occurs when the script tries to read user input but encounters an End-of-File (EOF) condition. This typically happens when:

1. **Non-interactive environment**: Running in VS Code's integrated terminal, IDE output panels, or automated scripts
2. **Stdin redirection**: When input is redirected or piped from another source
3. **Background execution**: When the script runs without a proper terminal session

### ✅ Solutions

#### Option 1: Use the Runner Script (Recommended)
```bash
# Test the setup
python run_agent.py --test

# Run interactively (ensures proper terminal detection)
python run_agent.py
```

#### Option 2: Use Direct Interactive Execution
```bash
# Run directly in Command Prompt or PowerShell
python main_azure_ai_dynamic.py

# Test mode to verify setup
python main_azure_ai_dynamic.py --test
```

#### Option 3: Use Windows Terminal or Command Prompt
- Open **Windows Terminal** or **Command Prompt**
- Navigate to the agent directory
- Run the script directly

### 🔧 Technical Details

The script now includes:

1. **Interactive Environment Detection**: Checks if running in a proper terminal using `sys.stdin.isatty()`
2. **EOF Error Handling**: Gracefully handles EOF conditions with proper cleanup
3. **Test Mode**: `--test` flag to verify setup without requiring interactive input
4. **Better Error Messages**: Clear guidance on how to run correctly

### 🚀 Recommended Workflow

1. **First Time Setup**:
   ```bash
   python run_agent.py --test
   ```

2. **Interactive Use**:
   ```bash
   python run_agent.py
   ```

3. **If Still Having Issues**:
   - Use Windows Terminal or Command Prompt directly
   - Avoid VS Code's integrated terminal for interactive sessions
   - Check environment variables are set correctly

### 📝 Environment Variables Required

```powershell
# PowerShell
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.cognitiveservices.azure.com/openai/deployments/gpt-4o"
$env:AZURE_OPENAI_API_KEY = "your-api-key"

# Command Prompt
set AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/openai/deployments/gpt-4o
set AZURE_OPENAI_API_KEY=your-api-key
```

### 🎯 Expected Output

When working correctly, you should see:
```
🧪 Running in test mode...
✓ Azure MCP Server initialized
✓ GitHub MCP Server initialized
🔧 Loaded 29 Azure tools
✅ Azure AI Inference Dynamic Agent initialized successfully!
```

For interactive mode:
```
🤖 Infrastructure Agent with Azure AI Inference & Dynamic Tool Loading
💡 Tools will be loaded automatically based on your conversation context
🚀 Using Azure AI Inference Client for improved performance
📝 Type 'exit' to quit, 'tools' to see loaded tools

Prompt: 
```
