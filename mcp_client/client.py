import requests
from typing import List, Dict, Any
import json

class MCPClient:
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url

    def get_tools(self) -> List[Dict[str, Any]]:
        """Fetch available tools from MCP server"""
        try:
            response = requests.get(f"{self.server_url}/mcp/tools", timeout=5)
            response.raise_for_status()
            tools = response.json()
            print(f"📡 Fetched {len(tools)} tools from MCP server")
            return tools
        except requests.RequestException as e:
            raise Exception(f"Failed to connect to MCP server at {self.server_url}: {str(e)}")

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Execute a tool on the MCP server"""
        try:
            print(f"🔧 Executing '{tool_name}' with: {parameters}")
            
            response = requests.post(
                f"{self.server_url}/mcp/execute",
                json={"tool_name": tool_name, "parameters": parameters},
                timeout=300
            )
            response.raise_for_status()
            
            result = response.json().get("result")
            print(f"✅ Tool result: {result}")
            return result
            
        except requests.RequestException as e:
            raise Exception(f"Tool execution failed: {str(e)}")
