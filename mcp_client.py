import json
import httpx
from config import Config

class MCPClient:
    def __init__(self, url: str):
        self.url = url

    def call_tool(self, tool_name: str, arguments: dict):
        """
        Simplified for production: In real MCP, use mcp.client.ClientSession.

        Calls a tool on the MCP server and returns the parsed JSON response.
        Raises RuntimeError with a helpful message if the server is unreachable
        or returns a non-JSON response (the most common cause of
        `json.decoder.JSONDecodeError: Expecting value: line 1 column 1`).
        """
        # Make sure the MCP server (FastAPI/uvicorn) is running at this URL.
        try:
            response = httpx.post(
                f"{self.url}/tools/{tool_name}",
                json=arguments,
                timeout=60.0,
            )
        except httpx.ConnectError as e:
            raise RuntimeError(
                f"Could not connect to MCP server at {self.url}. "
                f"Is the server running? (Start it with: python mcp_server.py)"
            ) from e
        except httpx.RequestError as e:
            raise RuntimeError(
                f"Network error while calling MCP tool '{tool_name}': {e}"
            ) from e

        # Surface HTTP errors (4xx / 5xx) with the response body for debugging.
        if response.status_code >= 400:
            snippet = response.text[:500] if response.text else "<empty body>"
            raise RuntimeError(
                f"MCP server returned HTTP {response.status_code} for tool "
                f"'{tool_name}': {snippet}"
            )

        # Only parse JSON when the body is actually JSON; otherwise raise a
        # clear error instead of letting json() throw a confusing JSONDecodeError.
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            snippet = response.text[:500] if response.text else "<empty body>"
            raise RuntimeError(
                f"MCP server returned a non-JSON response "
                f"(content-type: {content_type or 'unknown'}) for tool "
                f"'{tool_name}': {snippet}"
            )

        try:
            return response.json()
        except (json.JSONDecodeError, ValueError) as e:
            snippet = response.text[:500] if response.text else "<empty body>"
            raise RuntimeError(
                f"Failed to parse JSON response from MCP server for tool "
                f"'{tool_name}': {snippet}"
            ) from e
