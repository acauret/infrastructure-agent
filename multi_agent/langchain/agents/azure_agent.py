"""
Azure Infrastructure Agent
Specializes in Azure infrastructure analysis, monitoring, and management using LangChain
"""
import asyncio
from typing import Dict, List, Any, Optional

from .base_agent import BaseAgent, AgentConfig
from langchain_core.tools import tool
import sys
import os

# Add the parent directory to path to import MCP servers
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'agent'))

from azure_mcp_server import AzureMCPServer

class AzureInfrastructureAgent(BaseAgent):
    """Specialized agent for Azure infrastructure operations using LangChain"""
    
    def __init__(self, endpoint: str, api_key: str, model_name: str = "gpt-4"):
        config = AgentConfig(
            name="AzureInfrastructure",
            model_name=model_name,
            system_prompt=self._get_system_prompt(),
            endpoint=endpoint,
            api_key=api_key,
            temperature=0.1
        )
        super().__init__(config)
        self.azure_server: Optional[AzureMCPServer] = None
    
    def _get_system_prompt(self) -> str:
        """Get specialized system prompt for Azure infrastructure"""
        return """You are an Azure Infrastructure Expert Agent powered by LangChain.

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

You have access to comprehensive Azure tools through MCP (Model Context Protocol).
Be thorough, technical, and provide specific Azure CLI or PowerShell commands when helpful.
Explain complex concepts clearly and prioritize security and cost efficiency.

When users ask for comprehensive analysis, automatically perform complete infrastructure discovery."""
    
    async def _load_tools(self):
        """Load Azure MCP server tools and convert to LangChain tools"""
        try:
            self.logger.info("🔵 Loading Azure MCP server...")
            self.azure_server = AzureMCPServer()
            await self.azure_server.initialize()
            
            # Get MCP tools and create LangChain wrapper tools
            azure_tools = self.azure_server.list_tools()
            self.logger.info(f"🔵 Loaded {len(azure_tools)} Azure MCP tools:")
            
            # Create LangChain tools that wrap MCP tools
            for tool_name, tool_desc in azure_tools:
                self.logger.info(f"   - {tool_name}: {tool_desc}")
                # Create a LangChain tool wrapper
                langchain_tool = self._create_langchain_tool(tool_name, tool_desc)
                self.tools.append(langchain_tool)
                
        except Exception as e:
            self.logger.error(f"❌ Failed to load Azure tools: {e}")
            raise
    
    def _create_langchain_tool(self, tool_name: str, tool_description: str):
        """Create a LangChain tool that wraps an MCP tool"""
        
        @tool(name=tool_name, description=tool_description)
        async def azure_tool_wrapper(arguments: Dict[str, Any] = None) -> str:
            """Wrapper for Azure MCP tool"""
            if arguments is None:
                arguments = {}
            return await self.call_azure_tool(tool_name, arguments)
        
        return azure_tool_wrapper
    
    def _get_mcp_capabilities(self) -> List[str]:
        """Get MCP tool names for capabilities"""
        if self.azure_server:
            return [tool[0] for tool in self.azure_server.list_tools()]
        return []
    
    async def analyze_subscription(self, subscription_id: Optional[str] = None) -> str:
        """Perform comprehensive subscription analysis using LangChain"""
        if not self.azure_server:
            return "Azure server not initialized"
        
        try:
            self.logger.info("🔍 Starting comprehensive Azure subscription analysis...")
            
            # Get subscription details
            sub_details = await self.azure_server.call_tool("get_subscription_details", {})
            
            # Get resource groups
            resource_groups = await self.azure_server.call_tool("list_resource_groups", {})
            
            # Get all resources
            all_resources = await self.azure_server.call_tool("list_all_resources", {})
            
            # Analyze network topology
            vnets = await self.azure_server.call_tool("list_virtual_networks", {})
            
            # Use LangChain to analyze and synthesize the data
            analysis_prompt = f"""
Analyze this Azure infrastructure data and provide comprehensive insights:

SUBSCRIPTION DETAILS:
{sub_details}

RESOURCE GROUPS:
{resource_groups}

ALL RESOURCES:
{all_resources}

VIRTUAL NETWORKS:
{vnets}

Provide a detailed analysis covering:
1. Subscription overview and health
2. Resource organization and governance
3. Network architecture and security
4. Cost optimization opportunities
5. Security recommendations
6. Compliance insights
7. Actionable next steps
"""
            
            # Process through LangChain for intelligent analysis
            chain = self.prompt_template | self.llm
            analysis = await chain.ainvoke({"input": analysis_prompt})
            
            return analysis.content if hasattr(analysis, 'content') else str(analysis)
            
        except Exception as e:
            self.logger.error(f"❌ Analysis failed: {e}")
            return f"Analysis failed: {str(e)}"
    
    async def call_azure_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a specific Azure tool"""
        if not self.azure_server:
            return "Azure server not initialized"
        
        try:
            self.logger.info(f"🔧 Calling Azure tool: {tool_name}")
            result = await self.azure_server.call_tool(tool_name, arguments)
            self.logger.info(f"✅ Tool {tool_name} completed")
            return result
        except Exception as e:
            self.logger.error(f"❌ Tool {tool_name} failed: {e}")
            return f"Tool execution failed: {str(e)}"
    
    async def process_request(self, request: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Enhanced request processing with smart tool usage"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            self.logger.info(f"📝 Azure agent processing: {request[:100]}...")
            
            # Check if this is a comprehensive analysis request
            analysis_keywords = ["analyze", "subscription", "overview", "complete", "full", "comprehensive"]
            if any(keyword in request.lower() for keyword in analysis_keywords):
                return await self.analyze_subscription()
            
            # For other requests, use the base LangChain processing
            return await super().process_request(request, context)
            
        except Exception as e:
            self.logger.error(f"❌ Azure agent error: {e}")
            return f"Error: {str(e)}"
    
    async def shutdown(self):
        """Clean shutdown with Azure server cleanup"""
        if self.azure_server:
            try:
                await self.azure_server.close()
                self.logger.info("🔵 Azure MCP server closed")
            except Exception as e:
                self.logger.warning(f"⚠️ Azure server cleanup warning: {e}")
        
        await super().shutdown()
