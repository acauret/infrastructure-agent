"""
Multi-Agent Orchestration Engine
Coordinates multiple specialized agents using LangChain and Azure AI Inference
"""
import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

# Import specialized agents
import sys
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.azure_agent import AzureInfrastructureAgent
from agents.github_agent import GitHubAgent

# Load environment variables
load_dotenv()

class TaskType(Enum):
    """Types of tasks the orchestrator can handle"""
    AZURE_INFRASTRUCTURE = "azure_infrastructure"
    GITHUB_OPERATIONS = "github_operations"
    CROSS_PLATFORM = "cross_platform"
    GENERAL_INQUIRY = "general_inquiry"

@dataclass
class Task:
    """Represents a task to be executed"""
    id: str
    type: TaskType
    description: str
    assigned_agent: Optional[str] = None
    status: str = "pending"
    result: Optional[str] = None

class MultiAgentOrchestrator:
    """Main orchestration engine for multi-agent system using LangChain"""
    
    def __init__(self):
        self.logger = logging.getLogger("Orchestrator")
        
        # Initialize configuration from environment
        self.endpoint = os.getenv("AZURE_AI_INFERENCE_ENDPOINT")
        self.api_key = os.getenv("AZURE_AI_INFERENCE_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
        
        if not self.endpoint or not self.api_key:
            raise ValueError("Missing Azure AI Inference endpoint or API key")
        
        # Initialize orchestrator LLM (using larger model for decision making)
        self.orchestrator_llm = AzureAIChatCompletionsModel(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.api_key),
            model="Mistral-Large-2411",  # Use larger model for orchestration
            temperature=0.1,
        )
        
        # Create LangChain prompt templates
        self.classification_template = ChatPromptTemplate.from_messages([
            ("system", "You are a task classifier. Respond with just the category name."),
            ("human", self._get_classification_prompt())
        ])
        
        self.synthesis_template = ChatPromptTemplate.from_messages([
            ("system", "You are synthesizing responses from multiple specialized agents."),
            ("human", self._get_synthesis_prompt())
        ])
        
        self.orchestrator_template = ChatPromptTemplate.from_messages([
            ("system", self._get_orchestrator_prompt()),
            ("human", "{input}")
        ])
        
        # Initialize specialized agents
        self.agents: Dict[str, Any] = {}
        self.active_tasks: Dict[str, Task] = {}
        self.conversation_history: List[Any] = []
        
    def _get_classification_prompt(self) -> str:
        """Get classification prompt template"""
        return """Classify this request into ONE category:

AZURE_INFRASTRUCTURE: Azure subscription, resources, networking, security, monitoring
GITHUB_OPERATIONS: GitHub repositories, pull requests, issues, actions, workflows
CROSS_PLATFORM: Requires both Azure and GitHub (Infrastructure as Code, deployments)
GENERAL_INQUIRY: General questions not requiring specific tools

Request: {request}

Respond with just the category name."""
    
    def _get_synthesis_prompt(self) -> str:
        """Get synthesis prompt template"""
        return """Synthesize these responses from multiple agents into a coherent answer:

Azure Infrastructure Agent Response:
{azure_response}

GitHub Agent Response:  
{github_response}

Original Request: {original_request}

Provide a unified, comprehensive response that combines insights from both agents."""
    
    async def initialize(self):
        """Initialize all agents and the orchestration system"""
        try:
            self.logger.info("🚀 Initializing Multi-Agent Orchestration System with LangChain...")
            
            # Initialize Azure Infrastructure Agent
            self.logger.info("🔵 Setting up Azure Infrastructure Agent...")
            self.agents["azure"] = AzureInfrastructureAgent(
                endpoint=self.endpoint,
                api_key=self.api_key,
                model_name="gpt-4"  # Use GPT-4 for complex Azure analysis
            )
            await self.agents["azure"].initialize()
            
            # Initialize GitHub Agent  
            self.logger.info("🐙 Setting up GitHub Agent...")
            self.agents["github"] = GitHubAgent(
                endpoint=self.endpoint,
                api_key=self.api_key,
                model_name="mistral-small"  # Use smaller model for GitHub ops
            )
            await self.agents["github"].initialize()
            
            # Set orchestrator conversation history
            self.conversation_history = [
                SystemMessage(content=self._get_orchestrator_prompt())
            ]
            
            self.logger.info("✅ Multi-Agent System Ready!")
            self._print_system_status()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize orchestrator: {e}")
            raise
    
    def _get_orchestrator_prompt(self) -> str:
        """Get system prompt for the orchestrator"""
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
    
    async def process_request(self, user_input: str) -> str:
        """Process user request and coordinate agent responses using LangChain"""
        try:
            self.logger.info(f"📝 Processing request: {user_input[:100]}...")
            
            # Classify the request using LangChain
            task_type = await self._classify_request(user_input)
            self.logger.info(f"🎯 Classified as: {task_type.value}")
            
            # Route to appropriate agent(s)
            response = await self._route_request(user_input, task_type)
            
            # Add to conversation history
            self.conversation_history.extend([
                HumanMessage(content=user_input),
                AIMessage(content=response)
            ])
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Error processing request: {e}")
            return f"Error processing request: {str(e)}"
    
    async def _classify_request(self, request: str) -> TaskType:
        """Classify the type of request using LangChain"""
        try:
            # Create classification chain
            classification_chain = self.classification_template | self.orchestrator_llm
            
            # Run classification
            response = await classification_chain.ainvoke({"request": request})
            
            # Extract content
            classification = response.content.strip().upper() if hasattr(response, 'content') else str(response).strip().upper()
            
            # Map response to TaskType
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
    
    async def _route_request(self, request: str, task_type: TaskType) -> str:
        """Route request to appropriate agent(s) using LangChain"""
        
        if task_type == TaskType.AZURE_INFRASTRUCTURE:
            # Pure Azure request
            self.logger.info("🔵 Routing to Azure Infrastructure Agent")
            return await self.agents["azure"].process_request(request)
        
        elif task_type == TaskType.GITHUB_OPERATIONS:
            # Pure GitHub request
            self.logger.info("🐙 Routing to GitHub Agent")
            return await self.agents["github"].process_request(request)
        
        elif task_type == TaskType.CROSS_PLATFORM:
            # Cross-platform request - coordinate multiple agents
            self.logger.info("🔀 Cross-platform request - coordinating multiple agents")
            return await self._handle_cross_platform_request(request)
        
        else:
            # General inquiry - handle with orchestrator
            self.logger.info("💭 General inquiry - handling with orchestrator")
            return await self._handle_general_inquiry(request)
    
    async def _handle_cross_platform_request(self, request: str) -> str:
        """Handle requests that require multiple agents using LangChain synthesis"""
        try:
            # Get responses from both agents
            azure_response = await self.agents["azure"].process_request(request)
            github_response = await self.agents["github"].process_request(request)
            
            # Use LangChain to synthesize responses
            synthesis_chain = self.synthesis_template | self.orchestrator_llm
            
            synthesis = await synthesis_chain.ainvoke({
                "azure_response": azure_response,
                "github_response": github_response,
                "original_request": request
            })
            
            return synthesis.content if hasattr(synthesis, 'content') else str(synthesis)
            
        except Exception as e:
            self.logger.error(f"Cross-platform synthesis failed: {e}")
            # Fallback to simple concatenation
            return f"Azure Response:\n{azure_response}\n\nGitHub Response:\n{github_response}"
    
    async def _handle_general_inquiry(self, request: str) -> str:
        """Handle general inquiries with the orchestrator using LangChain"""
        try:
            orchestrator_chain = self.orchestrator_template | self.orchestrator_llm
            response = await orchestrator_chain.ainvoke({"input": request})
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            self.logger.error(f"General inquiry failed: {e}")
            return f"I can help with Azure infrastructure and GitHub operations. Error: {str(e)}"
    
    def _print_system_status(self):
        """Print system status"""
        print("\n" + "="*60)
        print("🤖 MULTI-AGENT INFRASTRUCTURE SYSTEM (LangChain)")
        print("="*60)
        azure_tools = len(self.agents['azure'].get_capabilities()) if 'azure' in self.agents else 0
        github_tools = len(self.agents['github'].get_capabilities()) if 'github' in self.agents else 0
        print(f"🔵 Azure Infrastructure Agent (LangChain + GPT-4): {azure_tools} tools")
        print(f"🐙 GitHub Agent (LangChain + Mistral-Small): {github_tools} tools")
        print(f"🧠 Orchestrator: LangChain + Mistral-Large-2411")
        print("="*60)
        print("💡 Try:")
        print("  'analyze my Azure subscription comprehensively'")
        print("  'check my GitHub repositories and activity'")
        print("  'show complete infrastructure and development status'")
        print("="*60)
    
    async def shutdown(self):
        """Clean shutdown of all agents"""
        self.logger.info("🔄 Shutting down Multi-Agent System...")
        
        for name, agent in self.agents.items():
            try:
                await agent.shutdown()
            except Exception as e:
                self.logger.warning(f"⚠️ Warning during {name} agent shutdown: {e}")
        
        self.logger.info("✅ Multi-Agent System shutdown complete")

async def main():
    """Main entry point for LangChain multi-agent system"""
    
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
    
    # Initialize orchestrator
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
            
            # Process request through orchestrator
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
