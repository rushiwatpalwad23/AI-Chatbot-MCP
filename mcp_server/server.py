import sys
import os
# Add the parent directory to Python path so we can import mcp_server
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn

# Import tools directly from the same directory
from tools import CalculatorTool, TemperatureTool, GeminiWebSearchTool

app = FastAPI(
    title="MCP Server for AI Tools", 
    version="1.0.0",
    description="Model Context Protocol server providing tools for AI applications"
)

class ToolCallRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]

class ToolDescription(BaseModel):
    name: str
    description: str
    parameters: List[Dict[str, Any]]

# Initialize tools
tools = {
    "calculator": CalculatorTool(),
    "get_temperature": TemperatureTool(),
    "gemini_web_search": GeminiWebSearchTool(),
}

@app.get("/")
async def root():
    return {
        "message": "MCP Server is running with Ollama + Qwen3", 
        "available_endpoints": ["/mcp/tools", "/mcp/execute"],
        "tools_count": len(tools)
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "tools": list(tools.keys())}

@app.get("/mcp/tools", response_model=List[ToolDescription])
async def get_tools():
    """Return available tools for discovery"""
    print("📡 Client requested available tools")
    return [
        {
            "name": "calculator",
            "description": "Performs basic arithmetic operations (add, subtract, multiply, divide)",
            "parameters": [
                {"name": "operation", "type": "string", "description": "Operation: add, subtract, multiply, divide", "required": True},
                {"name": "a", "type": "float", "description": "First number", "required": True},
                {"name": "b", "type": "float", "description": "Second number", "required": True}
            ]
        },
        {
            "name": "get_temperature",
            "description": "Gets current temperature for a given place",
            "parameters": [
                {"name": "place_name", "type": "string", "description": "City name (e.g., Pune, Mumbai, Delhi)", "required": True}
            ]
        },
        {
            "name": "gemini_web_search",
            "description": "Performs real-time web search using Gemini AI for latest information and current events",
            "parameters": [
                {"name": "query", "type": "string", "description": "Search query or question requiring latest information", "required": True},
                {"name": "max_length", "type": "string", "description": "Content length: short, medium, long", "required": False}
            ]
        }
    ]

@app.post("/mcp/execute")
async def execute_tool(request: ToolCallRequest):
    """Execute the specified tool with given parameters"""
    print(f"🔧 Executing tool: {request.tool_name}")
    print(f"📋 Parameters: {request.parameters}")
    
    tool = tools.get(request.tool_name)
    if not tool:
        print(f"❌ Tool '{request.tool_name}' not found")
        available_tools = list(tools.keys())
        raise HTTPException(
            status_code=404, 
            detail=f"Tool '{request.tool_name}' not found. Available tools: {available_tools}"
        )
    
    try:
        result = tool.execute(request.parameters)
        print(f"✅ Tool execution successful: {result}")
        return {"result": result}
    except Exception as e:
        print(f"❌ Tool execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting MCP Server for Ollama + Qwen3...")
    print("Server will be available at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
