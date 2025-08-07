"""
Simplified Multi-Agent Orchestration Engine (No LangChain Dependencies)
Coordinates multiple specialized agents using Azure AI Inference directly
"""
import asyncio
import json
import logging
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

# Import specialized agents
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'agent'))
from azure_mcp_server import AzureMCPServer
from github_mcp_server import GitHubMCPServer

# Load environment variables
load_dotenv()

class TaskType(Enum):
    """Types of tasks the orchestrator can handle"""
    AZURE_INFRASTRUCTURE = "azure_infrastructure"
    GITHUB_OPERATIONS = "github_operations"
    CROSS_PLATFORM = "cross_platform"
    GENERAL_INQUIRY = "general_inquiry"

@dataclass
class AgentConfig:
    """Configuration for an agent"""
    name: str
    model_name: str
    system_prompt: str
    endpoint: str
    api_key: str

class SpecializedAgent:
    """Base class for specialized agents"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = logging.getLogger(f"Agent.{config.name}")
        
        # Create Azure AI Inference client
        self.client = ChatCompletionsClient(
            endpoint=config.endpoint,
            credential=AzureKeyCredential(config.api_key)
        )
        
        self.conversation_history = [
            SystemMessage(content=config.system_prompt)
        ]
        
    async def process_request(self, request: str) -> str:
        """Process request and return response"""
        try:
            self.logger.info(f"📝 {self.config.name} processing: {request[:100]}...")
            
            # Add user message
            messages = self.conversation_history + [UserMessage(content=request)]
            
            # Get response from Azure AI
            response = self.client.complete(messages=messages, model=self.config.model_name)
            
            content = response.choices[0].message.content
            self.logger.info(f"✅ {self.config.name} generated response")
            
            return content
            
        except Exception as e:
            self.logger.error(f"❌ {self.config.name} error: {e}")
            return f"Error: {str(e)}"

class AzureInfrastructureAgent(SpecializedAgent):
    """Azure Infrastructure specialized agent"""
    
    def __init__(self, endpoint: str, api_key: str):
        config = AgentConfig(
            name="AzureInfrastructure",
            model_name="gpt-4",
            system_prompt="""You are an Azure Infrastructure Expert Agent.

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

Be thorough, technical, and provide specific Azure CLI or PowerShell commands when helpful.""",
            endpoint=endpoint,
            api_key=api_key
        )
        super().__init__(config)
        self.azure_server: Optional[AzureMCPServer] = None
        
    async def initialize(self):
        """Initialize Azure MCP server"""
        try:
            self.logger.info("🔵 Initializing Azure MCP server...")
            self.azure_server = AzureMCPServer()
            await self.azure_server.initialize()
            
            tools = self.azure_server.list_tools()
            self.logger.info(f"🔵 Loaded {len(tools)} Azure tools")
            
        except Exception as e:
            self.logger.error(f"❌ Azure MCP initialization failed: {e}")
            raise
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call Azure MCP tool"""
        if not self.azure_server:
            return "Azure server not initialized"
        
        try:
            self.logger.info(f"🔧 Calling Azure tool: {tool_name}")
            result = await self.azure_server.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            return f"Tool error: {str(e)}"
    
    async def analyze_subscription(self) -> str:
        """Comprehensive subscription analysis"""
        results = []
        
        try:
            # Get subscription details
            sub_details = await self.call_tool("get_subscription_details", {})
            results.append(f"📊 SUBSCRIPTION DETAILS:\n{sub_details}")
            
            # Get resource groups
            rgs = await self.call_tool("list_resource_groups", {})
            results.append(f"\n📁 RESOURCE GROUPS:\n{rgs}")
            
            # Get all resources
            resources = await self.call_tool("list_all_resources", {})
            results.append(f"\n🔧 ALL RESOURCES:\n{resources}")
            
            # Get virtual networks
            vnets = await self.call_tool("list_virtual_networks", {})
            results.append(f"\n🌐 VIRTUAL NETWORKS:\n{vnets}")
            
            return "\n".join(results)
            
        except Exception as e:
            return f"Analysis failed: {str(e)}"
    
    async def shutdown(self):
        """Clean shutdown"""
        if self.azure_server:
            try:
                await self.azure_server.close()
            except Exception as e:
                self.logger.warning(f"Azure server cleanup warning: {e}")

class GitHubAgent(SpecializedAgent):
    """GitHub specialized agent"""
    
    def __init__(self, endpoint: str, api_key: str):
        config = AgentConfig(
            name="GitHub",
            model_name="mistral-small",
            system_prompt="""You are a GitHub DevOps Expert Agent.

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

Be thorough with GitHub best practices and provide specific examples.""",
            endpoint=endpoint,
            api_key=api_key
        )
        super().__init__(config)
        self.github_server: Optional[GitHubMCPServer] = None
        
    async def initialize(self):
        """Initialize GitHub MCP server"""
        try:
            self.logger.info("🐙 Initializing GitHub MCP server...")
            self.github_server = GitHubMCPServer()
            await self.github_server.initialize()
            
            tools = self.github_server.list_tools()
            self.logger.info(f"🐙 Loaded {len(tools)} GitHub tools")
            
        except Exception as e:
            self.logger.error(f"❌ GitHub MCP initialization failed: {e}")
            raise
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call GitHub MCP tool"""
        if not self.github_server:
            return "GitHub server not initialized"
        
        try:
            self.logger.info(f"🔧 Calling GitHub tool: {tool_name}")
            result = await self.github_server.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            return f"Tool error: {str(e)}"
    
    async def shutdown(self):
        """Clean shutdown"""
        if self.github_server:
            try:
                await self.github_server.close()
            except Exception as e:
                self.logger.warning(f"GitHub server cleanup warning: {e}")

class MultiAgentOrchestrator:
    """Main orchestration engine"""
    
    def __init__(self):
        self.logger = logging.getLogger("Orchestrator")
        
        # Get configuration from environment
        self.endpoint = os.getenv("AZURE_AI_INFERENCE_ENDPOINT")
        self.api_key = os.getenv("AZURE_AI_INFERENCE_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
        
        if not self.endpoint or not self.api_key:
            raise ValueError("Missing Azure AI endpoint or API key")
        
        # Create orchestrator client
        self.client = ChatCompletionsClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.api_key)
        )
        
        # Initialize agents
        self.agents: Dict[str, SpecializedAgent] = {}
        
    async def initialize(self):
        """Initialize all agents"""
        try:
            self.logger.info("🚀 Initializing Multi-Agent System...")
            
            # Initialize Azure agent
            self.agents["azure"] = AzureInfrastructureAgent(self.endpoint, self.api_key)
            await self.agents["azure"].initialize()
            
            # Initialize GitHub agent
            self.agents["github"] = GitHubAgent(self.endpoint, self.api_key)
            await self.agents["github"].initialize()
            
            self.logger.info("✅ Multi-Agent System Ready!")
            self._print_status()
            
        except Exception as e:
            self.logger.error(f"❌ Initialization failed: {e}")
            raise
    
    async def process_request(self, user_input: str) -> str:
        """Process user request through appropriate agent(s)"""
        try:
            # Classify request
            task_type = await self._classify_request(user_input)
            self.logger.info(f"🎯 Classified as: {task_type.value}")
            
            # Route to appropriate handler
            if task_type == TaskType.AZURE_INFRASTRUCTURE:
                return await self._handle_azure_request(user_input)
            elif task_type == TaskType.GITHUB_OPERATIONS:
                return await self._handle_github_request(user_input)
            elif task_type == TaskType.CROSS_PLATFORM:
                return await self._handle_cross_platform_request(user_input)
            else:
                return await self._handle_general_request(user_input)
                
        except Exception as e:
            self.logger.error(f"❌ Request processing failed: {e}")
            return f"Error: {str(e)}"
    
    async def _classify_request(self, request: str) -> TaskType:
        """Classify request type"""
        prompt = f"""Classify this request into ONE category:

AZURE_INFRASTRUCTURE: Azure subscriptions, resources, networking, security
GITHUB_OPERATIONS: GitHub repos, pull requests, issues, actions
CROSS_PLATFORM: Needs both Azure and GitHub (IaC deployments)
GENERAL_INQUIRY: General questions not needing specific tools

Request: {request}

Respond with just the category name."""
        
        try:
            response = self.client.complete(
                messages=[
                    SystemMessage(content="You classify requests. Respond with just the category name."),
                    UserMessage(content=prompt)
                ],
                model="Mistral-Large-2411"
            )
            
            classification = response.choices[0].message.content.strip().upper()
            
            if "AZURE" in classification:
                return TaskType.AZURE_INFRASTRUCTURE
            elif "GITHUB" in classification:
                return TaskType.GITHUB_OPERATIONS
            elif "CROSS" in classification:
                return TaskType.CROSS_PLATFORM
            else:
                return TaskType.GENERAL_INQUIRY
                
        except Exception as e:
            self.logger.warning(f"Classification failed, defaulting to general: {e}")
            return TaskType.GENERAL_INQUIRY
    
    async def _handle_azure_request(self, request: str) -> str:
        """Handle Azure-specific requests"""
        self.logger.info("🔵 Routing to Azure Infrastructure Agent")
        
        # Check if this is a comprehensive analysis request
        if any(word in request.lower() for word in ["analyze", "subscription", "overview", "complete", "full"]):
            return await self.agents["azure"].analyze_subscription()
        else:
            return await self.agents["azure"].process_request(request)
    
    async def _handle_github_request(self, request: str) -> str:
        """Handle GitHub-specific requests"""
        self.logger.info("🐙 Routing to GitHub Agent")
        return await self.agents["github"].process_request(request)
    
    async def _handle_cross_platform_request(self, request: str) -> str:
        """Handle cross-platform requests"""
        self.logger.info("🔀 Cross-platform request - coordinating agents")
        
        # Get responses from both agents
        azure_response = await self.agents["azure"].process_request(request)
        github_response = await self.agents["github"].process_request(request)
        
        # Synthesize responses
        synthesis_prompt = f"""Combine these agent responses into one coherent answer:

AZURE AGENT RESPONSE:
{azure_response}

GITHUB AGENT RESPONSE:
{github_response}

ORIGINAL REQUEST: {request}

Provide a unified, comprehensive response."""
        
        try:
            response = self.client.complete(
                messages=[
                    SystemMessage(content="You synthesize responses from multiple agents into coherent answers."),
                    UserMessage(content=synthesis_prompt)
                ],
                model="Mistral-Large-2411"
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Azure Response:\n{azure_response}\n\nGitHub Response:\n{github_response}"
    
    async def _handle_general_request(self, request: str) -> str:
        """Handle general inquiries"""
        self.logger.info("💭 General inquiry")
        
        try:
            response = self.client.complete(
                messages=[
                    SystemMessage(content="You are a helpful assistant for Azure and GitHub infrastructure management."),
                    UserMessage(content=request)
                ],
                model="Mistral-Large-2411"
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"I can help with Azure infrastructure and GitHub operations. Error: {str(e)}"
    
    def _print_status(self):
        """Print system status"""
        print("\n" + "="*60)
        print("🤖 MULTI-AGENT INFRASTRUCTURE SYSTEM")
        print("="*60)
        print("🔵 Azure Infrastructure Agent: Ready")
        print("🐙 GitHub Agent: Ready")
        print("🧠 Orchestrator: Mistral-Large-2411")
        print("="*60)
        print("💡 Try:")
        print("  'analyze my Azure subscription'")
        print("  'list my GitHub repositories'")
        print("  'show infrastructure and code status'")
        print("="*60)
    
    async def shutdown(self):
        """Clean shutdown"""
        self.logger.info("🔄 Shutting down Multi-Agent System...")
        
        for name, agent in self.agents.items():
            try:
                await agent.shutdown()
            except Exception as e:
                self.logger.warning(f"Warning during {name} shutdown: {e}")
        
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
    
    orchestrator = MultiAgentOrchestrator()
    
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
