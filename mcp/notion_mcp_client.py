import httpx
from mcp.config import NOTION_API_KEY, NOTION_DATABASE_ID, NOTION_MCP_URL
from shared.utils.logging import get_logger

logger = get_logger(__name__)

class NotionMCPClient:
    """
    Model Context Protocol (MCP) client for Notion.
    Exposes an MCP-style tool call interface to interact with Notion.
    Uses the direct Notion API when NOTION_MCP_URL is not specified, 
    making it reliable and self-contained.
    """

    def __init__(self):
        self.api_key = NOTION_API_KEY
        self.database_id = NOTION_DATABASE_ID
        self.mcp_url = NOTION_MCP_URL
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

    def call_tool(self, name: str, arguments: dict) -> dict:
        """
        Executes an MCP tool call on the Notion datasource.
        If an MCP server is configured via URL, it forwards the request.
        Otherwise, it executes the tool logic directly against the Notion API.
        """
        logger.info(f"Notion MCP Tool Call: {name}")

        # If MCP server URL is provided, forward via HTTP JSON-RPC
        if self.mcp_url:
            try:
                rpc_payload = {
                    "jsonrpc": "2.0",
                    "method": name,
                    "params": arguments,
                    "id": 1
                }
                with httpx.Client() as client:
                    response = client.post(self.mcp_url, json=rpc_payload, timeout=10.0)
                    response.raise_for_status()
                    result = response.json()
                    if "error" in result:
                        raise ValueError(f"MCP Server Error: {result['error']}")
                    return result.get("result", {})
            except Exception as e:
                logger.warning(f"Failed to call external MCP server: {e}. Falling back to direct Notion API.")

        # Fallback to direct Notion API calls
        return self._execute_direct_api(name, arguments)

    def _execute_direct_api(self, tool_name: str, arguments: dict) -> dict:
        """Translates MCP tool calls to raw Notion REST API calls."""
        if tool_name == "notion_create_page" or tool_name == "create_page":
            return self._notion_create_page(arguments)
        elif tool_name == "notion_update_page_properties" or tool_name == "update_page_properties":
            return self._notion_update_page_properties(arguments)
        elif tool_name == "notion_query_database" or tool_name == "query_database":
            return self._notion_query_database(arguments)
        else:
            raise NotImplementedError(f"Tool {tool_name} is not implemented in direct Notion client fallback.")

    def _notion_create_page(self, arguments: dict) -> dict:
        url = "https://api.notion.com/v1/pages"
        parent = arguments.get("parent", {})
        
        # Default parent to our configured database if not specified
        if "database_id" not in parent and "page_id" not in parent:
            parent = {"database_id": self.database_id}

        payload = {
            "parent": parent,
            "properties": arguments.get("properties", {})
        }
        
        if "children" in arguments:
            payload["children"] = arguments["children"]

        with httpx.Client() as client:
            response = client.post(url, json=payload, headers=self.headers, timeout=15.0)
            if response.status_code >= 400:
                logger.error(f"Notion API error: {response.status_code} - {response.text}")
            response.raise_for_status()
            return response.json()

    def _notion_update_page_properties(self, arguments: dict) -> dict:
        page_id = arguments.get("page_id")
        if not page_id:
            raise ValueError("page_id is required for notion_update_page_properties")

        url = f"https://api.notion.com/v1/pages/{page_id}"
        payload = {
            "properties": arguments.get("properties", {})
        }

        with httpx.Client() as client:
            response = client.patch(url, json=payload, headers=self.headers, timeout=15.0)
            if response.status_code >= 400:
                logger.error(f"Notion API error: {response.status_code} - {response.text}")
            response.raise_for_status()
            return response.json()

    def _notion_query_database(self, arguments: dict) -> dict:
        database_id = arguments.get("database_id", self.database_id)
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        payload = {}
        if "filter" in arguments:
            payload["filter"] = arguments["filter"]

        with httpx.Client() as client:
            response = client.post(url, json=payload, headers=self.headers, timeout=15.0)
            if response.status_code >= 400:
                logger.error(f"Notion API error: {response.status_code} - {response.text}")
            response.raise_for_status()
            return response.json()
