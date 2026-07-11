import os
from dotenv import load_dotenv

load_dotenv()

# Notion credentials
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")

# MCP Server integration settings
# If a direct Notion MCP JSON-RPC server is running, we can specify its URL.
# Otherwise, we fall back to the direct Notion API client implementation.
NOTION_MCP_URL = os.getenv("NOTION_MCP_URL", "")
