#!/usr/bin/env python3
"""Simple main app with just Azure MCP server"""

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
from agent.azure_mcp_server import AzureMCPServer
import json, os, logging, asyncio, sys
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)
load_dotenv()

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")

# Ensure the endpoint has https:// protocol
if AZURE_OPENAI_ENDPOINT and not AZURE_OPENAI_ENDPOINT.startswith(('http://', 'https://')):
    AZURE_OPENAI_ENDPOINT = f"https://{AZURE_OPENAI_ENDPOINT}"

# Validate configuration
if not AZURE_OPENAI_ENDPOINT:
    raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is not set")

# Initialize Azure credentials
credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(
    credential, "https://cognitiveservices.azure.com/.default"
)

async def run():
    # Initialize Azure OpenAI client
    client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version="2024-04-01-preview",
        azure_ad_token_provider=token_provider,
    )

    # Initialize Azure MCP Server only
    azure_mcp_server = AzureMCPServer()
    
    async with azure_mcp_server.create_session():
        # Display available tools from Azure MCP
        azure_tools = azure_mcp_server.list_tools()
        print(f"Loaded {len(azure_tools)} Azure MCP tools:")
        for tool_name, tool_desc in azure_tools:
            short_desc = tool_desc.split('.')[0] if '.' in tool_desc else tool_desc[:60]
            print(f"  • {tool_name}: {short_desc}")

        available_tools = azure_mcp_server.formatted_tools
        print(f"\nTotal tools available: {len(available_tools)}")
        print("\nReady for conversation. Type 'exit' to quit.")

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
