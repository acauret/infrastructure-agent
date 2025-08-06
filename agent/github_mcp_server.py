"""GitHub MCP Server Module for GitHub Tools Integration"""

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class GitHubMCPServer:
    """Server for managing GitHub MCP (Model Context Protocol) connections and tool calls"""
    
    def __init__(self, command: str = "docker", args: List[str] = None, env: Dict[str, str] = None):
        """Initialize GitHub MCP server with Docker parameters
        
        Args:
            command: Command to run the MCP server (default: "docker")
            args: Arguments for the MCP server command
            env: Environment variables to pass to the MCP server
        """
        self.command = command
        self.args = args or [
            "run",
            "-i",
            "--rm",
            "-e",
            "GITHUB_PERSONAL_ACCESS_TOKEN",
            "ghcr.io/github/github-mcp-server",
            "stdio"
        ]
        
        # Set up environment with GitHub token
        github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_PERSONAL_ACCESS_TOKEN environment variable is required")
        
        self.env = env or {**os.environ}
        self.env["GITHUB_PERSONAL_ACCESS_TOKEN"] = github_token
        
        self._session: Optional[ClientSession] = None
        self._read = None
        self._write = None
        self._tools = None
        self._formatted_tools = None
        self._stdio_context = None

    @property
    def session(self) -> Optional[ClientSession]:
        """Get the current MCP session"""
        return self._session

    @property
    def tools(self) -> Optional[List[Any]]:
        """Get the list of available tools"""
        return self._tools

    @property
    def formatted_tools(self) -> Optional[List[Dict[str, Any]]]:
        """Get tools formatted for OpenAI"""
        return self._formatted_tools

    async def initialize(self) -> None:
        """Initialize the MCP server and session"""
        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=self.env
            )
            
            # Start the stdio client and store the context manager
            self._stdio_context = stdio_client(server_params)
            self._read, self._write = await self._stdio_context.__aenter__()
            
            # Create and initialize session
            self._session = ClientSession(self._read, self._write)
            await self._session.__aenter__()
            await self._session.initialize()
            
            logger.info("GitHub MCP Server initialized successfully")
            
            # Load available tools
            await self._load_tools()
            
        except Exception as e:
            logger.error(f"Failed to initialize GitHub MCP Server: {e}")
            raise

    async def _load_tools(self) -> None:
        """Load and format available tools"""
        if not self._session:
            raise RuntimeError("Session not initialized")
            
        tools_response = await self._session.list_tools()
        self._tools = tools_response.tools
        
        # Format tools for OpenAI
        self._formatted_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in self._tools
        ]
        
        logger.info(f"Loaded {len(self._tools)} GitHub MCP tools")

    def list_tools(self) -> List[Tuple[str, str]]:
        """List available tools with their descriptions
        
        Returns:
            List of (name, description) tuples
        """
        if not self._tools:
            return []
        return [(tool.name, tool.description) for tool in self._tools]

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a specific tool with arguments
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            String representation of the tool result
        """
        if not self._session:
            raise RuntimeError("Session not initialized")
            
        try:
            logger.info(f"Calling GitHub MCP tool: {tool_name}")
            logger.debug(f"Tool arguments: {arguments}")
            
            result = await self._session.call_tool(tool_name, arguments)
            
            # Extract content from result
            if hasattr(result, 'content'):
                if isinstance(result.content, list) and len(result.content) > 0:
                    # Handle list of content items
                    content_items = []
                    for item in result.content:
                        if hasattr(item, 'text'):
                            content_items.append(item.text)
                        else:
                            content_items.append(str(item))
                    content = "\n".join(content_items)
                else:
                    content = str(result.content)
            else:
                content = str(result)
            
            logger.info(f"Tool {tool_name} completed successfully")
            return content
            
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            raise

    async def close(self) -> None:
        """Close the MCP session and clean up resources"""
        cleanup_errors = []
        
        # Close session first
        if self._session:
            try:
                await asyncio.wait_for(
                    self._session.__aexit__(None, None, None),
                    timeout=2.0
                )
            except (asyncio.TimeoutError, asyncio.CancelledError, RuntimeError) as e:
                cleanup_errors.append(f"Session close {type(e).__name__}")
            except Exception as e:
                cleanup_errors.append(f"Session close: {e}")
            finally:
                self._session = None
        
        # Close stdio context with shorter timeout and better error handling
        if self._stdio_context:
            try:
                await asyncio.wait_for(
                    self._stdio_context.__aexit__(None, None, None),
                    timeout=2.0
                )
            except (asyncio.TimeoutError, asyncio.CancelledError, RuntimeError) as e:
                cleanup_errors.append(f"Stdio context {type(e).__name__}")
                # Force cleanup by setting to None
            except Exception as e:
                cleanup_errors.append(f"Stdio context: {e}")
            finally:
                self._stdio_context = None
            
        self._read = None
        self._write = None
        
        if cleanup_errors:
            logger.warning(f"GitHub MCP Server close warnings: {'; '.join(cleanup_errors)}")
        else:
            logger.info("GitHub MCP Server closed successfully")

    @asynccontextmanager
    async def create_session(self):
        """Context manager for GitHub MCP Server session"""
        try:
            await self.initialize()
            yield self
        finally:
            try:
                await self.close()
            except Exception as e:
                logger.warning(f"Error during cleanup: {e}")
                # Continue with cleanup, don't raise
