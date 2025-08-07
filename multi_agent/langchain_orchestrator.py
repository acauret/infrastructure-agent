"""
LangChain Multi-Agent Orchestration Engine (Working Version)
Coordinates multiple specialized agents using LangChain and Azure AI Inference
"""
import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import sys

# Add paths for MCP server imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agent'))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TaskType(Enum):
    """Types of tasks the orchestrator can handle"""
    AZURE_INFRASTRUCTURE = "azure_infrastructure"
    GITHUB_OPERATIONS = "github_operations"
    CROSS_PLATFORM = "cross_platform"
    GENERAL_INQUIRY = "general_inquiry"

class LangChainAgent:
    """Base LangChain agent with Azure AI Inference"""
    
    def __init__(self, name: str, model: str, system_prompt: str, endpoint: str, api_key: str):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.endpoint = endpoint
        self.api_key = api_key
        self.logger = logging.getLogger(f"Agent.{name}")
        
        # Will be initialized in async init
        self.llm = None
        self.prompt_template = None
        self.chain = None
        
    async def initialize(self):
        """Initialize LangChain components"""
        try:
            from langchain_openai import AzureChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate
            
            self.logger.info(f"🚀 Initializing {self.name} with LangChain...")
            
            # Get temperature from environment with fallback
            temperature = float(os.getenv("MODEL_TEMPERATURE", "0.1"))
            max_tokens = int(os.getenv("MODEL_MAX_TOKENS", "4000"))
            
            # Initialize Azure OpenAI model
            self.llm = AzureChatOpenAI(
                azure_endpoint=self.endpoint,
                api_key=self.api_key,
                azure_deployment=self.model,  # This is the deployment name
                api_version="2024-12-01-preview",
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Create prompt template
            self.prompt_template = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                ("human", "{input}")
            ])
            
            # Create chain
            self.chain = self.prompt_template | self.llm
            
            self.logger.info(f"✅ {self.name} LangChain agent ready! (Model: {self.model}, Temp: {temperature})")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize {self.name}: {e}")
            raise
    
    async def process(self, request: str) -> str:
        """Process request using LangChain"""
        try:
            if not self.chain:
                await self.initialize()
            
            self.logger.info(f"📝 {self.name} processing: {request[:100]}...")
            
            response = await self.chain.ainvoke({"input": request})
            content = response.content if hasattr(response, 'content') else str(response)
            
            self.logger.info(f"✅ {self.name} response generated ({len(content)} chars)")
            return content
            
        except Exception as e:
            self.logger.error(f"❌ {self.name} processing error: {e}")
            return f"Error in {self.name}: {str(e)}"

class AzureLangChainAgent(LangChainAgent):
    """Azure Infrastructure Agent with LangChain and MCP integration"""
    
    def __init__(self, endpoint: str, api_key: str):
        system_prompt = """You are an Azure Infrastructure Expert Agent powered by LangChain.

Your expertise includes:
- Azure subscription and resource management
- Virtual networks, subnets, and security groups analysis
- Resource group organization and governance
- Azure monitoring and cost optimization
- Infrastructure as Code (ARM, Bicep, Terraform)
- Security best practices and compliance

When analyzing infrastructure:
1. Always get subscription details first
2. Analyze resource groups and their resources
3. Review network topology and security configurations
4. Identify optimization opportunities
5. Provide actionable recommendations

Be thorough, technical, and provide specific Azure CLI or PowerShell commands when helpful.
Explain complex concepts clearly and prioritize security and cost efficiency."""
        
        # Get model from environment with fallback
        model = os.getenv("AZURE_AGENT_MODEL", "gpt-4")
        
        super().__init__(
            name="AzureInfrastructure",
            model=model,
            system_prompt=system_prompt,
            endpoint=endpoint,
            api_key=api_key
        )
        
        self.azure_server = None
    
    async def initialize(self):
        """Initialize LangChain and Azure MCP server"""
        await super().initialize()
        
        try:
            from azure_mcp_server import AzureMCPServer
            
            self.logger.info("🔵 Loading Azure MCP server...")
            self.azure_server = AzureMCPServer()
            await self.azure_server.initialize()
            
            azure_tools = self.azure_server.list_tools()
            self.logger.info(f"🔵 Loaded {len(azure_tools)} Azure MCP tools")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load Azure MCP: {e}")
            # Continue without MCP tools
    
    async def process(self, request: str) -> str:
        """Enhanced processing with Azure tools"""
        # Check if this is a comprehensive analysis request
        analysis_keywords = ["analyze", "subscription", "overview", "complete", "comprehensive", "list"]
        if any(keyword in request.lower() for keyword in analysis_keywords):
            return await self.simple_analysis(request)
        
        # Use LangChain for other requests
        return await super().process(request)
    
    async def simple_analysis(self, request: str) -> str:
        """Simple analysis using basic Azure tools"""
        if not self.azure_server:
            return await super().process(f"Analyze Azure infrastructure: {request}")
        
        try:
            self.logger.info("🔍 Starting simple Azure analysis...")
            
            # Try to call a simple tool first
            try:
                # Use the extension_az tool which is basically Azure CLI
                result = await self.azure_server.call_tool("extension_az", {
                    "command": "account show"
                })
                self.logger.info(f"📊 Azure CLI result: {len(str(result))} chars")
                
                if result and len(str(result)) > 50:
                    # We got real data, analyze it with LangChain
                    analysis_prompt = f"""Analyze this Azure account information and provide insights:

AZURE ACCOUNT INFO:
{result}

Based on this information, provide:
1. Account and subscription overview
2. Current subscription details
3. Any recommendations or insights
4. Summary of what we can see

Request: {request}"""
                    
                    response = await self.chain.ainvoke({"input": analysis_prompt})
                    return response.content if hasattr(response, 'content') else str(response)
                else:
                    # Fallback to intelligent analysis without data
                    return await super().process(f"Provide Azure infrastructure analysis for: {request}")
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Azure CLI tool failed: {e}")
                return await super().process(f"Analyze Azure infrastructure (tools unavailable): {request}")
                
        except Exception as e:
            self.logger.error(f"❌ Analysis failed: {e}")
            return f"Analysis error: {str(e)}"
    
    async def shutdown(self):
        """Clean shutdown"""
        if self.azure_server:
            try:
                await self.azure_server.close()
                self.logger.info("🔵 Azure MCP server closed")
            except Exception as e:
                self.logger.warning(f"⚠️ Azure server cleanup warning: {e}")

class GitHubLangChainAgent(LangChainAgent):
    """GitHub Agent with LangChain and MCP integration"""
    
    def __init__(self, endpoint: str, api_key: str):
        system_prompt = """You are a GitHub DevOps Expert Agent powered by LangChain.

Your expertise includes:
- GitHub repository management and organization
- CI/CD pipelines with GitHub Actions
- Code review and collaboration workflows
- Branch strategies and release management
- Security scanning and vulnerability management
- GitHub Apps and integrations
- Infrastructure as Code repositories

When working with repositories:
1. Always understand the repository structure first
2. Review recent commits and pull requests
3. Check CI/CD pipeline status and configurations
4. Analyze security and compliance posture
5. Provide actionable improvement suggestions

Be thorough with GitHub best practices and provide specific examples.
Focus on automation, security, and developer productivity."""
        
        # Get model from environment with fallback
        model = os.getenv("GITHUB_AGENT_MODEL", "mistral-small")
        
        super().__init__(
            name="GitHub",
            model=model,
            system_prompt=system_prompt,
            endpoint=endpoint,
            api_key=api_key
        )
        
        self.github_server = None
    
    async def initialize(self):
        """Initialize LangChain and GitHub MCP server"""
        await super().initialize()
        
        try:
            # Import and initialize GitHub MCP server
            import sys
            import os
            sys.path.append(os.path.dirname(__file__))
            
            from agent.github_mcp_server import GitHubMCPServer
            
            self.logger.info("🐙 Loading GitHub MCP server...")
            self.github_server = GitHubMCPServer()
            await self.github_server.initialize()
            
            github_tools = self.github_server.list_tools()
            self.logger.info(f"🐙 Loaded {len(github_tools)} GitHub MCP tools")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load GitHub MCP: {e}")
            # Continue without MCP tools
    
    async def shutdown(self):
        """Clean shutdown"""
        if self.github_server:
            try:
                await self.github_server.close()
                self.logger.info("🐙 GitHub MCP server closed")
            except Exception as e:
                self.logger.warning(f"⚠️ GitHub server cleanup warning: {e}")

class LangChainOrchestrator:
    """Main orchestration engine using LangChain"""
    
    def __init__(self):
        self.logger = logging.getLogger("Orchestrator")
        
        # Get configuration
        self.endpoint = os.getenv("AZURE_AI_INFERENCE_ENDPOINT")
        self.api_key = os.getenv("AZURE_AI_INFERENCE_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
        
        if not self.endpoint or not self.api_key:
            raise ValueError("Missing Azure AI Inference endpoint or API key")
        
        # Initialize orchestrator agent
        self.orchestrator = LangChainAgent(
            name="Orchestrator",
            model=os.getenv("ORCHESTRATOR_MODEL", "Mistral-Large-2411"),
            system_prompt=self._get_orchestrator_prompt(),
            endpoint=self.endpoint,
            api_key=self.api_key
        )
        
        # Initialize specialized agents
        self.agents = {}
    
    def _get_orchestrator_prompt(self) -> str:
        """Get orchestrator system prompt"""
        return """You are the Multi-Agent Orchestration Engine for Infrastructure Management using LangChain.

Your role is to:
1. Analyze user requests and determine which specialized agent(s) should handle them
2. Break down complex requests into subtasks
3. Coordinate between agents when cross-platform operations are needed
4. Synthesize results from multiple agents into coherent responses

Available Agents:
- Azure Infrastructure Agent (LangChain + GPT-4): Azure subscription, resources, networking, security analysis
- GitHub Agent (LangChain + Mistral-Small): Repository management, CI/CD, DevOps workflows

Task Classification:
- AZURE_INFRASTRUCTURE: Pure Azure operations (resources, networking, monitoring)
- GITHUB_OPERATIONS: Pure GitHub operations (repos, PRs, issues, actions)  
- CROSS_PLATFORM: Requires both Azure and GitHub (IaC repos, deployments)
- GENERAL_INQUIRY: General questions not requiring specific tools

Always be clear about which agent is handling what, and provide comprehensive analysis.
Leverage LangChain's capabilities for intelligent reasoning and tool orchestration."""
    
    async def initialize(self):
        """Initialize all agents"""
        try:
            self.logger.info("🚀 Initializing LangChain Multi-Agent System...")
            
            # Initialize orchestrator
            await self.orchestrator.initialize()
            
            # Initialize Azure agent
            self.agents["azure"] = AzureLangChainAgent(self.endpoint, self.api_key)
            await self.agents["azure"].initialize()
            
            # Initialize GitHub agent
            self.agents["github"] = GitHubLangChainAgent(self.endpoint, self.api_key)
            await self.agents["github"].initialize()
            
            self.logger.info("✅ LangChain Multi-Agent System Ready!")
            self._print_status()
            
        except Exception as e:
            self.logger.error(f"❌ Initialization failed: {e}")
            raise
    
    async def process_request(self, user_input: str) -> str:
        """Process request through orchestrator"""
        try:
            self.logger.info(f"📝 Processing: {user_input[:100]}...")
            
            # Classify request
            task_type = await self._classify_request(user_input)
            self.logger.info(f"🎯 Classified as: {task_type.value}")
            
            # Route to appropriate agent
            if task_type == TaskType.AZURE_INFRASTRUCTURE:
                self.logger.info("🔵 Routing to Azure Infrastructure Agent")
                return await self.agents["azure"].process(user_input)
            
            elif task_type == TaskType.GITHUB_OPERATIONS:
                self.logger.info("🐙 Routing to GitHub Agent")
                return await self.agents["github"].process(user_input)
            
            elif task_type == TaskType.CROSS_PLATFORM:
                self.logger.info("🔀 Cross-platform request - coordinating agents")
                return await self._handle_cross_platform(user_input)
            
            else:
                self.logger.info("💭 General inquiry - handling with orchestrator")
                return await self.orchestrator.process(user_input)
                
        except Exception as e:
            self.logger.error(f"❌ Request processing failed: {e}")
            return f"Error: {str(e)}"
    
    async def _classify_request(self, request: str) -> TaskType:
        """Classify request type"""
        classification_prompt = f"""Classify this request into ONE category:

AZURE_INFRASTRUCTURE: Azure subscriptions, resources, networking, security
GITHUB_OPERATIONS: GitHub repos, pull requests, issues, actions
CROSS_PLATFORM: Needs both Azure and GitHub (IaC deployments)
GENERAL_INQUIRY: General questions not needing specific tools

Request: {request}

Respond with just the category name."""
        
        try:
            response = await self.orchestrator.process(classification_prompt)
            
            classification = response.strip().upper()
            if "AZURE" in classification:
                return TaskType.AZURE_INFRASTRUCTURE
            elif "GITHUB" in classification:
                return TaskType.GITHUB_OPERATIONS
            elif "CROSS" in classification:
                return TaskType.CROSS_PLATFORM
            else:
                return TaskType.GENERAL_INQUIRY
                
        except Exception as e:
            self.logger.warning(f"Classification failed: {e}")
            return TaskType.GENERAL_INQUIRY
    
    async def _handle_cross_platform(self, request: str) -> str:
        """Handle cross-platform requests"""
        try:
            # Get responses from both agents
            azure_response = await self.agents["azure"].process(request)
            github_response = await self.agents["github"].process(request)
            
            # Synthesize with orchestrator
            synthesis_prompt = f"""Synthesize these responses into a coherent answer:

Azure Response: {azure_response}

GitHub Response: {github_response}

Original Request: {request}

Provide a unified, comprehensive response."""
            
            return await self.orchestrator.process(synthesis_prompt)
            
        except Exception as e:
            return f"Cross-platform processing error: {str(e)}"
    
    def _print_status(self):
        """Print system status"""
        print("\n" + "="*60)
        print("🤖 LANGCHAIN MULTI-AGENT INFRASTRUCTURE SYSTEM")
        print("="*60)
        print("🔵 Azure Infrastructure Agent (LangChain + GPT-4 + MCP)")
        print("🐙 GitHub Agent (LangChain + Mistral-Small + MCP)")
        print("🧠 Orchestrator (LangChain + Mistral-Large-2411)")
        print("="*60)
        print("💡 Try:")
        print("  'analyze my Azure subscription comprehensively'")
        print("  'check my GitHub repositories and activity'")
        print("  'show complete infrastructure and development status'")
        print("="*60)
    
    async def shutdown(self):
        """Clean shutdown"""
        self.logger.info("🔄 Shutting down LangChain Multi-Agent System...")
        
        for name, agent in self.agents.items():
            try:
                await agent.shutdown()
            except Exception as e:
                self.logger.warning(f"⚠️ Warning during {name} shutdown: {e}")
        
        self.logger.info("✅ Shutdown complete")

async def main():
    """Main entry point"""
    
    # Configure logging
    log_level = os.getenv("LOG_LEVEL", "WARNING").upper()
    if log_level == "NONE":
        logging.basicConfig(level=logging.CRITICAL + 1)
    else:
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        logging.basicConfig(
            level=level_map.get(log_level, logging.WARNING),
            format='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
    
    orchestrator = LangChainOrchestrator()
    
    try:
        await orchestrator.initialize()
        
        # Main conversation loop
        while True:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            response = await orchestrator.process_request(user_input)
            print(f"\nAssistant: {response}")
    
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
    except Exception as e:
        print(f"\nERROR: {e}")
    
    finally:
        await orchestrator.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
