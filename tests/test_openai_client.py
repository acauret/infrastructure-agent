#!/usr/bin/env python3
"""Test Azure OpenAI client separately"""

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")

# Ensure the endpoint has https:// protocol
if AZURE_OPENAI_ENDPOINT and not AZURE_OPENAI_ENDPOINT.startswith(('http://', 'https://')):
    AZURE_OPENAI_ENDPOINT = f"https://{AZURE_OPENAI_ENDPOINT}"

print(f"Endpoint: {AZURE_OPENAI_ENDPOINT}")
print(f"Model: {AZURE_OPENAI_MODEL}")

try:
    print("Creating Azure credentials...")
    credential = DefaultAzureCredential()
    
    print("Creating token provider...")
    token_provider = get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )
    
    print("Creating Azure OpenAI client...")
    client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version="2024-04-01-preview",
        azure_ad_token_provider=token_provider,
    )
    
    print("Azure OpenAI client created successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
