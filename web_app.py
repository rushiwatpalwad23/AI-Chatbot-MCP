from flask import Flask, render_template, request, jsonify
import json
import ollama
import re
import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_client.client import MCPClient

app = Flask(__name__)

# Global variables for the AI components
mcp_client = None
ollama_client = None
config = None

def extract_json_from_response(response_text):
    """Extract JSON object from response text that may contain other content"""
    try:
        cleaned_text = re.sub(r'<Thinking>.*?</Thinking>', '', response_text, flags=re.DOTALL | re.IGNORECASE)
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, cleaned_text)
        
        for match in matches:
            try:
                parsed = json.loads(match)
                if "tool_name" in parsed and "parameters" in parsed:
                    return parsed
            except json.JSONDecodeError:
                continue
        return None
    except Exception:
        return None

def initialize_ai_components():
    """Initialize Ollama and MCP client"""
    global mcp_client, ollama_client, config
    
    try:
        # Load configuration
        with open("config/config.json", "r") as f:
            config = json.load(f)
        
        # Initialize MCP client
        mcp_client = MCPClient(config["mcp_server"]["host"])
        tools = mcp_client.get_tools()
        
        # Initialize Ollama client
        ollama_client = ollama.Client(host=config["ollama"]["host"])
        
        # Test connection
        test_response = ollama_client.chat(
            model=config["ollama"]["model"],
            messages=[{"role": "user", "content": "Test"}],
            options={"num_predict": 5}
        )
        
        print("✅ AI components initialized successfully!")
        print(f"✅ Connected to MCP server with {len(tools)} tools")
        print(f"✅ Connected to Ollama with model: {config['ollama']['model']}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize AI components: {str(e)}")
        return False

@app.route('/')
def index():
    """Serve the main chat interface"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        print(f"💬 User message: {user_message}")
        
        # Get available tools
        tools = mcp_client.get_tools()
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in tools])
        
        # Create prompt for tool decision
        decision_prompt = f"""
Available tools:
{tool_descriptions}

User query: {user_message}

If this query needs a tool, respond with ONLY this JSON format:
{{"tool_name": "exact_tool_name", "parameters": {{"param": "value"}}}}

If no tool is needed, respond with: NO_TOOL_NEEDED

Examples:
- "What's 5 + 3?" → {{"tool_name": "calculator", "parameters": {{"operation": "add", "a": 5, "b": 3}}}}
- "Temperature in Pune" → {{"tool_name": "get_temperature", "parameters": {{"place_name": "Pune"}}}}
- "Latest AI developments" → {{"tool_name": "gemini_web_search", "parameters": {{"query": "latest AI developments 2024"}}}}
- "WTC 2025 final" → {{"tool_name": "gemini_web_search", "parameters": {{"query": "WTC 2025 final Australia South Africa"}}}}
- "Hello" → NO_TOOL_NEEDED

Response:"""

        ollama_options = {
            "temperature": config["ollama"]["temperature"],
            "top_p": config["ollama"]["top_p"],
            "top_k": config["ollama"]["top_k"],
            "num_ctx": config["ollama"]["num_ctx"],
            "num_predict": config["ollama"]["num_predict"]
        }
        
        # Step 1: Ask AI to decide on tool usage
        print("🔍 Asking AI for tool decision...")
        decision_response = ollama_client.chat(
            model=config["ollama"]["model"],
            messages=[{"role": "user", "content": decision_prompt}],
            options=ollama_options
        )
        
        decision_content = decision_response["message"]["content"].strip()
        print(f"🧠 AI decision: {decision_content}")
        
        # Step 2: Check if tool is needed
        if "NO_TOOL_NEEDED" in decision_content.upper():
            # Direct response without tools
            print("💬 No tool needed, generating direct response...")
            direct_prompt = f"User asked: {user_message}\n\nProvide a helpful, friendly answer:"
            
            direct_response = ollama_client.chat(
                model=config["ollama"]["model"],
                messages=[{"role": "user", "content": direct_prompt}],
                options=ollama_options
            )
            
            return jsonify({
                'content': direct_response['message']['content'],
                'toolCalls': []
            })
            
        else:
            # Try to extract tool call
            tool_call = extract_json_from_response(decision_content)
            
            if tool_call:
                print(f"🔧 Tool call extracted: {tool_call}")
                try:
                    # Step 3: Execute the tool via MCP
                    print(f"🚀 Executing tool: {tool_call['tool_name']} with params: {tool_call['parameters']}")
                    tool_result = mcp_client.execute_tool(
                        tool_call["tool_name"], 
                        tool_call["parameters"]
                    )
                    print(f"🔍 Tool result received: {len(tool_result)} characters")
                    print(f"📄 Tool result preview: {tool_result[:200]}...")
                    
                    # Step 4: Generate final answer using tool result - IMPROVED PROMPT
                    final_prompt = f"""
The user asked: "{user_message}"

I used the {tool_call['tool_name']} tool and received this information:

TOOL RESULT:
{tool_result}

IMPORTANT INSTRUCTIONS:
1. Use ONLY the information from the tool result above to answer the user's question
2. Do NOT ignore the tool result or say the information is unavailable
3. If the tool result contains specific facts, dates, scores, or details, include them in your response
4. Be conversational and helpful
5. Summarize the key information from the tool result clearly
6. If the tool result shows that an event has happened, report it as factual information

Based on the tool result above, provide a complete and accurate answer to the user's question:"""

                    print("🤖 Generating final response with tool result...")
                    final_response = ollama_client.chat(
                        model=config["ollama"]["model"],
                        messages=[{"role": "user", "content": final_prompt}],
                        options={
                            **ollama_options,
                            "temperature": 0.3,  # Lower temperature for more factual responses
                            "num_predict": 500   # Allow longer responses
                        }
                    )
                    
                    final_content = final_response['message']['content']
                    print(f"✅ Final response generated: {len(final_content)} characters")
                    print(f"📝 Final response preview: {final_content[:200]}...")
                    
                    return jsonify({
                        'content': final_content,
                        'toolCalls': [{
                            'name': tool_call['tool_name'],
                            'parameters': tool_call['parameters'],
                            'result': tool_result[:500] + "..." if len(tool_result) > 500 else tool_result
                        }]
                    })
                    
                except Exception as tool_error:
                    print(f"❌ Tool execution error: {str(tool_error)}")
                    # Fallback response
                    fallback_prompt = f"User asked: {user_message}\n\nI encountered an error while trying to get current information: {str(tool_error)}\n\nPlease provide a helpful response explaining this limitation and suggest alternative ways to find the information:"
                    
                    fallback_response = ollama_client.chat(
                        model=config["ollama"]["model"],
                        messages=[{"role": "user", "content": fallback_prompt}],
                        options=ollama_options
                    )
                    
                    return jsonify({
                        'content': fallback_response['message']['content'],
                        'toolCalls': [],
                        'error': f'Tool execution failed: {str(tool_error)}'
                    })
                    
            else:
                print("⚠️ Could not extract tool call, providing direct response...")
                # Fallback to direct response
                direct_prompt = f"User asked: {user_message}\n\nProvide a helpful answer:"
                
                direct_response = ollama_client.chat(
                    model=config["ollama"]["model"],
                    messages=[{"role": "user", "content": direct_prompt}],
                    options=ollama_options
                )
                
                return jsonify({
                    'content': direct_response['message']['content'],
                    'toolCalls': []
                })
                
    except Exception as e:
        print(f"❌ Chat API error: {str(e)}")
        return jsonify({'error': f'Failed to process request: {str(e)}'}), 500

@app.route('/api/status')
def status():
    """Check system status"""
    try:
        # Check MCP server
        tools = mcp_client.get_tools()
        print(f"📡 Fetched {len(tools)} tools from MCP server")
        
        # Check Ollama
        test_response = ollama_client.chat(
            model=config["ollama"]["model"],
            messages=[{"role": "user", "content": "Test"}],
            options={"num_predict": 5}
        )
        
        return jsonify({
            'status': 'healthy',
            'mcp_server': 'connected',
            'ollama': 'connected',
            'model': config["ollama"]["model"],
            'tools_available': len(tools)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting AI Web Interface...")
    print("=" * 50)
    
    if initialize_ai_components():
        print("🌐 Web interface starting at: http://localhost:5000")
        print("🔧 Make sure MCP server is running at: http://localhost:8000")
        print("🔍 Make sure Gemini service is running at: http://localhost:2024")
        print("=" * 50)
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("❌ Failed to start web interface")
        print("Make sure:")
        print("1. Ollama is running: ollama serve")
        print("2. MCP server is running: python mcp_server/server.py")
        print("3. Gemini service is running on localhost:2024")
        print("4. Config file exists: config/config.json")
