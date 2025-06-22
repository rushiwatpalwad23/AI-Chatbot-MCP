# AI Tool Calling Application
## Ollama + Qwen3 + MCP Architecture

A pure Python AI application that uses Ollama with Qwen3 model and Model Context Protocol (MCP) for tool calling.

## Features
- 🤖 **Ollama + Qwen3**: Local AI model (no OpenAI needed)
- 🔧 **MCP Tools**: Calculator and Weather tools
- 🏠 **100% Local**: No external API dependencies
- 🚀 **Fast Setup**: Automated installation script

## Quick Start

### 1. Setup (Run Once)
\`\`\`bash
python setup.py
\`\`\`

### 2. Run Application (3 Terminals)

**Terminal 1 - Ollama:**
\`\`\`bash
ollama serve
\`\`\`

**Terminal 2 - MCP Server:**
\`\`\`bash
python mcp_server/server.py
\`\`\`

**Terminal 3 - Main App:**
\`\`\`bash
python app.py
\`\`\`

## Test Queries
- `What is 25 + 17?` (Calculator tool)
- `Tell me the temperature in Pune` (Weather tool)
- `Hello!` (Direct response, no tool)

## Project Structure
\`\`\`
├── app.py                 # Main application
├── mcp_client/           # MCP client package
│   ├── __init__.py
│   └── client.py
├── mcp_server/           # MCP server package
│   ├── __init__.py
│   ├── server.py         # FastAPI server
│   └── tools.py          # Tool implementations
├── config/
│   ├── config.json       # Configuration
│   └── modelfile         # Ollama model config
├── setup.py              # Setup script
├── requirements.txt      # Dependencies
└── README.md
\`\`\`

## How It Works
1. **User Query** → Main app (`app.py`)
2. **Tool Decision** → Ollama + Qwen3 decides if tool needed
3. **Tool Execution** → MCP Client → MCP Server → Tool
4. **Final Answer** → Qwen3 generates response using tool result

## Requirements
- Python 3.8+
- Ollama installed and running
- Internet connection (for initial model download)

## Troubleshooting
- **Ollama not found**: Install from https://ollama.ai
- **Model not found**: Run `python setup.py` again
- **Connection refused**: Make sure all 3 terminals are running
