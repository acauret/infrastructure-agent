"""
GitHub Agent
Specializes in GitHub repository management, CI/CD, and DevOps operations using LangChain
"""
import asyncio
from typing import Dict, List, Any, Optional

from .base_agent import BaseAgent, AgentConfig
from langchain_core.tools import tool
import sys
import os

# Add the parent directory to path to import MCP servers
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'agent'))

from github_mcp_server import GitHubMCPServer

class GitHubAgent(BaseAgent):
    """Specialized agent for GitHub operations using LangChain"""
    
    def __init__(self, endpoint: str, api_key: str, model_name: str = "mistral-small"):
        config = AgentConfig(
            name="GitHub",
            model_name=model_name,
            system_prompt=self._get_system_prompt(),
            endpoint=endpoint,
            api_key=api_key,
            temperature=0.1
        )
        super().__init__(config)
        self.github_server: Optional[GitHubMCPServer] = None
    
    def _get_system_prompt(self) -> str:
        """Get specialized system prompt for GitHub operations"""
        return """You are a GitHub DevOps Expert Agent powered by LangChain.

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

You have access to comprehensive GitHub tools through MCP (Model Context Protocol).
Be thorough with GitHub best practices and provide specific examples.
Focus on automation, security, and developer productivity.

When users ask for repository analysis, automatically perform comprehensive discovery."""
    
    async def _load_tools(self):
        """Load GitHub MCP server tools and convert to LangChain tools"""
        try:
            self.logger.info("🐙 Loading GitHub MCP server...")
            self.github_server = GitHubMCPServer()
            await self.github_server.initialize()
            
            # Get MCP tools and create LangChain wrapper tools
            github_tools = self.github_server.list_tools()
            self.logger.info(f"🐙 Loaded {len(github_tools)} GitHub MCP tools:")
            
            # Create LangChain tools that wrap MCP tools
            for tool_name, tool_desc in github_tools:
                self.logger.info(f"   - {tool_name}: {tool_desc}")
                # Create a LangChain tool wrapper
                langchain_tool = self._create_langchain_tool(tool_name, tool_desc)
                self.tools.append(langchain_tool)
                
        except Exception as e:
            self.logger.error(f"❌ Failed to load GitHub tools: {e}")
            raise
    
    def _create_langchain_tool(self, tool_name: str, tool_description: str):
        """Create a LangChain tool that wraps an MCP tool"""
        
        @tool(name=tool_name, description=tool_description)
        async def github_tool_wrapper(arguments: Dict[str, Any] = None) -> str:
            """Wrapper for GitHub MCP tool"""
            if arguments is None:
                arguments = {}
            return await self.call_github_tool(tool_name, arguments)
        
        return github_tool_wrapper
    
    def _get_mcp_capabilities(self) -> List[str]:
        """Get MCP tool names for capabilities"""
        if self.github_server:
            return [tool[0] for tool in self.github_server.list_tools()]
        return []
    
    async def analyze_repository(self, repo_name: str, owner: Optional[str] = None) -> str:
        """Perform comprehensive repository analysis using LangChain"""
        if not self.github_server:
            return "GitHub server not initialized"
        
        try:
            self.logger.info(f"🔍 Starting GitHub repository analysis for {repo_name}...")
            
            # Get repository details
            repo_info = await self.github_server.call_tool("get_repository", {"name": repo_name})
            
            # Get recent commits
            commits = await self.github_server.call_tool("list_commits", {"repo": repo_name, "limit": 10})
            
            # Get pull requests
            prs = await self.github_server.call_tool("list_pull_requests", {"repo": repo_name})
            
            # Get issues
            issues = await self.github_server.call_tool("list_issues", {"repo": repo_name})
            
            # Use LangChain to analyze and synthesize the data
            analysis_prompt = f"""
Analyze this GitHub repository data and provide comprehensive insights:

REPOSITORY DETAILS:
{repo_info}

RECENT COMMITS:
{commits}

PULL REQUESTS:
{prs}

ISSUES:
{issues}

Provide a detailed analysis covering:
1. Repository health and activity
2. Development workflow analysis
3. Code quality and collaboration patterns
4. CI/CD pipeline assessment
5. Security and compliance review
6. Community engagement metrics
7. Actionable improvement recommendations
"""
            
            # Process through LangChain for intelligent analysis
            chain = self.prompt_template | self.llm
            analysis = await chain.ainvoke({"input": analysis_prompt})
            
            return analysis.content if hasattr(analysis, 'content') else str(analysis)
            
        except Exception as e:
            self.logger.error(f"❌ Repository analysis failed: {e}")
            return f"Analysis failed: {str(e)}"
    
    async def call_github_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a specific GitHub tool"""
        if not self.github_server:
            return "GitHub server not initialized"
        
        try:
            self.logger.info(f"🔧 Calling GitHub tool: {tool_name}")
            result = await self.github_server.call_tool(tool_name, arguments)
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
            self.logger.info(f"📝 GitHub agent processing: {request[:100]}...")
            
            # Check if this is a repository analysis request
            repo_keywords = ["repository", "repo", "analyze", "list", "overview"]
            if any(keyword in request.lower() for keyword in repo_keywords):
                # Try to extract repo name or use default behavior
                # For now, use the base LangChain processing
                pass
            
            # Use the base LangChain processing
            return await super().process_request(request, context)
            
        except Exception as e:
            self.logger.error(f"❌ GitHub agent error: {e}")
            return f"Error: {str(e)}"
    
    async def shutdown(self):
        """Clean shutdown with GitHub server cleanup"""
        if self.github_server:
            try:
                await self.github_server.close()
                self.logger.info("🐙 GitHub MCP server closed")
            except Exception as e:
                self.logger.warning(f"⚠️ GitHub server cleanup warning: {e}")
        
        await super().shutdown()
