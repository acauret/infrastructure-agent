# Model Configuration Guide

## 🎛️ **Configurable Models in Environment Variables**

You can now configure all AI models used by the LangChain Multi-Agent System through environment variables.

## 📁 **Environment File Configuration**

### 1. Create your `.env` file:
```bash
cp .env.example .env
```

### 2. Edit `.env` with your model preferences:

```bash
# Model Configuration for Agents
AZURE_AGENT_MODEL=gpt-4                 # Azure Infrastructure Agent
GITHUB_AGENT_MODEL=mistral-small        # GitHub Operations Agent  
ORCHESTRATOR_MODEL=Mistral-Large-2411   # Main Orchestrator

# Model Parameters
MODEL_TEMPERATURE=0.1     # Lower = more focused, Higher = more creative
MODEL_MAX_TOKENS=4000     # Maximum response length
```

## 🤖 **Available Models**

### **Azure AI Inference Models:**
- `gpt-4` - Most capable, best for complex analysis
- `gpt-4o` - Optimized GPT-4 variant
- `gpt-35-turbo` - Faster, cost-effective
- `Mistral-Large-2411` - Large multilingual model
- `mistral-small` - Efficient, fast responses  
- `llama-3-8b-instruct` - Meta's Llama model
- `cohere-command-r-plus` - Cohere's advanced model

### **Recommended Configurations:**

#### **Performance Optimized:**
```bash
AZURE_AGENT_MODEL=gpt-4                    # Best Azure analysis
GITHUB_AGENT_MODEL=mistral-small           # Fast GitHub ops
ORCHESTRATOR_MODEL=Mistral-Large-2411      # Intelligent routing
```

#### **Cost Optimized:**
```bash
AZURE_AGENT_MODEL=gpt-35-turbo             # More affordable
GITHUB_AGENT_MODEL=mistral-small           # Efficient
ORCHESTRATOR_MODEL=mistral-small           # Budget-friendly
```

#### **Speed Optimized:**
```bash
AZURE_AGENT_MODEL=mistral-small            # Fast responses
GITHUB_AGENT_MODEL=mistral-small           # Quick operations
ORCHESTRATOR_MODEL=mistral-small           # Rapid routing
```

## 🎯 **Model Selection Guidelines**

### **Azure Agent (Infrastructure Analysis):**
- **Recommended**: `gpt-4` - Complex infrastructure requires sophisticated reasoning
- **Alternative**: `gpt-35-turbo` - For simpler infrastructure setups
- **Budget**: `mistral-small` - Basic analysis capabilities

### **GitHub Agent (DevOps Operations):**
- **Recommended**: `mistral-small` - Fast, efficient for GitHub operations
- **Alternative**: `gpt-35-turbo` - More detailed analysis
- **Power**: `gpt-4` - Complex repository analysis

### **Orchestrator (Request Routing):**
- **Recommended**: `Mistral-Large-2411` - Excellent classification and routing
- **Alternative**: `gpt-4` - Superior reasoning for complex requests
- **Budget**: `mistral-small` - Basic routing capabilities

## ⚙️ **Advanced Configuration**

### **Temperature Settings:**
```bash
MODEL_TEMPERATURE=0.1    # Focused, deterministic (recommended)
MODEL_TEMPERATURE=0.3    # Balanced creativity and focus
MODEL_TEMPERATURE=0.7    # More creative, varied responses
```

### **Token Limits:**
```bash
MODEL_MAX_TOKENS=2000    # Shorter responses
MODEL_MAX_TOKENS=4000    # Standard responses (recommended)
MODEL_MAX_TOKENS=8000    # Detailed responses (if model supports)
```

## 🔄 **Runtime Model Switching**

You can change models without code changes:

1. **Update `.env` file**:
```bash
AZURE_AGENT_MODEL=gpt-35-turbo  # Switch from gpt-4
```

2. **Restart the system**:
```bash
python langchain_orchestrator.py
```

The new model will be loaded automatically!

## 📊 **Model Performance Comparison**

| Model | Speed | Quality | Cost | Best For |
|-------|-------|---------|------|----------|
| gpt-4 | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | Complex analysis |
| gpt-35-turbo | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Balanced performance |
| Mistral-Large-2411 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | Orchestration |
| mistral-small | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Fast operations |

## 🧪 **Testing Different Models**

Use the test script to compare models:

```bash
# Test with current configuration
python test_system.py

# Test with different model
MODEL_TEMPERATURE=0.3 python test_system.py
```

## 💡 **Tips**

1. **Start with recommended settings** and adjust based on your needs
2. **Higher temperature** for brainstorming, **lower temperature** for analysis
3. **Match model capability** to task complexity
4. **Monitor costs** with premium models like GPT-4
5. **Test performance** with your specific use cases

---

**🎛️ Full control over AI models through simple environment variables!**
