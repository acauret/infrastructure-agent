"""
Base Agent Class for Multi-Agent Infrastructure System
Provides common functionality for all specialized agents using LangChain
"""
import asyncio
import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class AgentConfig:
    """Configuration for an agent"""
    name: str
    model_name: str
    system_prompt: str
    endpoint: str
    api_key: str
    max_retries: int = 3
    temperature: float = 0.1

class BaseAgent(ABC):
    """Base class for all specialized agents using LangChain"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = logging.getLogger(f"Agent.{config.name}")
        
        # Initialize LangChain Azure AI model
        self.llm = AzureAIChatCompletionsModel(
            endpoint=config.endpoint,
            credential=AzureKeyCredential(config.api_key),
            model=config.model_name,
            temperature=config.temperature,
        )
        
        # Agent state
        self.tools: List[BaseTool] = []
        self.conversation_history: List[BaseMessage] = []
        self.is_initialized = False
        
        # Create chat prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", config.system_prompt),
            ("human", "{input}")
        ])
        
    async def initialize(self):
        """Initialize the agent and its tools"""
        try:
            self.logger.info(f"🚀 Initializing {self.config.name} agent...")
            
            # Load agent-specific tools
            await self._load_tools()
            
            # Set system prompt
            self.conversation_history = [
                SystemMessage(content=self.config.system_prompt)
            ]
            
            self.is_initialized = True
            self.logger.info(f"✅ {self.config.name} agent ready with {len(self.tools)} tools")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize {self.config.name}: {e}")
            raise
    
    @abstractmethod
    async def _load_tools(self):
        """Load agent-specific tools - implemented by subclasses"""
        pass
    
    async def process_request(self, request: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process a request and return response using LangChain"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            self.logger.info(f"📝 Processing request: {request[:100]}...")
            
            # Create the chain
            chain = self.prompt_template | self.llm
            
            # Invoke the chain
            response = await chain.ainvoke({"input": request})
            
            # Extract content based on response type
            if hasattr(response, 'content'):
                content = response.content
            elif isinstance(response, str):
                content = response
            else:
                content = str(response)
            
            # Add to conversation history
            self.conversation_history.extend([
                HumanMessage(content=request),
                AIMessage(content=content)
            ])
            
            self.logger.info(f"✅ Generated response ({len(content)} chars)")
            return content
            
        except Exception as e:
            self.logger.error(f"❌ Error processing request: {e}")
            return f"Error: {str(e)}"
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        capabilities = [tool.name for tool in self.tools]
        # Also include MCP tool capabilities if available
        if hasattr(self, '_get_mcp_capabilities'):
            capabilities.extend(self._get_mcp_capabilities())
        return capabilities
    
    async def shutdown(self):
        """Clean shutdown of agent resources"""
        self.logger.info(f"🔄 Shutting down {self.config.name} agent...")
        # Cleanup code here
        self.logger.info(f"✅ {self.config.name} agent shutdown complete")
