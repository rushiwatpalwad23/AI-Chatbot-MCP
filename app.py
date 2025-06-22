import json
import ollama
import re
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_client.client import MCPClient
import asyncio

def extract_json_from_response(response_text):
    """Extract JSON object from response text that may contain other content"""
    try:
        # Remove any thinking tags or extra content
        cleaned_text = re.sub(r'<Thinking>.*?</Thinking>', '', response_text, flags=re.DOTALL | re.IGNORECASE)
        cleaned_text = re.sub(r'<Thinking>.*?</Thinking>', '', cleaned_text, flags=re.DOTALL | re.IGNORECASE)
        
        # Try to find JSON object in the response
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, cleaned_text)
        
        for match in matches:
            try:
                parsed = json.loads(match)
                # Check if it's a tool call JSON
                if "tool_name" in parsed and "parameters" in parsed:
                    return parsed
            except json.JSONDecodeError:
                continue
        
        return None
    except Exception:
        return None

async def main():
    print("🚀 Starting AI Application with Ollama + Qwen3")
    print("=" * 60)
    
    # Load configuration
    try:
        with open("config/config.json", "r") as f:
            config = json.load(f)
        print("✅ Configuration loaded")
    except Exception as e:
        print(f"❌ Failed to load config: {str(e)}")
        return

    # Initialize MCP client
    try:
        mcp_client = MCPClient(config["mcp_server"]["host"])
        tools = mcp_client.get_tools()
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in tools])
        print("✅ Connected to MCP server successfully!")
    except Exception as e:
        print(f"❌ Failed to connect to MCP server: {str(e)}")
        print("Make sure the MCP server is running: python mcp_server/server.py")
        return

    # Configure Ollama
    try:
        ollama_client = ollama.Client(host=config["ollama"]["host"])
        model = config["ollama"]["model"]
        
        # Test Ollama connection
        test_response = ollama_client.chat(
            model=model,
            messages=[{"role": "user", "content": "Hello"}],
            options={"num_predict": 10}
        )
        print("✅ Connected to Ollama + Qwen3 successfully!")
        
    except Exception as e:
        print(f"❌ Failed to connect to Ollama: {str(e)}")
        print("Make sure:")
        print("1. Ollama is running: ollama serve")
        print("2. Model exists: ollama list")
        print("3. Run setup: python setup.py")
        return

    ollama_options = {
        "temperature": config["ollama"]["temperature"],
        "top_p": config["ollama"]["top_p"],
        "top_k": config["ollama"]["top_k"],
        "num_ctx": config["ollama"]["num_ctx"],
        "num_predict": config["ollama"]["num_predict"]
    }

    print("\n🤖 AI Assistant Ready!")
    print("Available tools:")
    print(tool_descriptions)
    print("\nType 'exit' to quit.")
    print("=" * 60)

    while True:
        user_input = input("\n💬 Ask me anything: ")
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("👋 Goodbye!")
            break

        # Create prompt for tool decision
        decision_prompt = f"""
Available tools:
{tool_descriptions}

User query: {user_input}

If this query needs a tool, respond with ONLY this JSON format:
{{"tool_name": "exact_tool_name", "parameters": {{"param": "value"}}}}

If no tool is needed, respond with: NO_TOOL_NEEDED

Examples:
- "What's 5 + 3?" → {{"tool_name": "calculator", "parameters": {{"operation": "add", "a": 5, "b": 3}}}}
- "Temperature in Pune" → {{"tool_name": "get_temperature", "parameters": {{"place_name": "Pune"}}}}
- "Hello" → NO_TOOL_NEEDED

Response:"""

        try:
            print("🔍 Analyzing your question...")
            
            # Step 1: Ask Qwen3 to decide on tool usage
            decision_response = ollama_client.chat(
                model=model,
                messages=[{"role": "user", "content": decision_prompt}],
                options=ollama_options
            )
            
            decision_content = decision_response["message"]["content"].strip()
            print(f"🧠 Qwen3 decision: {decision_content}")

            # Step 2: Check if tool is needed
            if "NO_TOOL_NEEDED" in decision_content.upper():
                # Direct response without tools
                direct_prompt = f"User asked: {user_input}\n\nProvide a helpful, friendly answer:"
                
                direct_response = ollama_client.chat(
                    model=model,
                    messages=[{"role": "user", "content": direct_prompt}],
                    options=ollama_options
                )
                
                print(f"\n💬 Answer: {direct_response['message']['content']}")
                
            else:
                # Try to extract tool call
                tool_call = extract_json_from_response(decision_content)
                
                if tool_call:
                    print(f"\n🔧 Using tool: {tool_call['tool_name']}")
                    print(f"📋 Parameters: {tool_call['parameters']}")
                    
                    try:
                        # Step 3: Execute the tool via MCP
                        tool_result = mcp_client.execute_tool(
                            tool_call["tool_name"], 
                            tool_call["parameters"]
                        )
                        print(f"🔍 Tool result: {tool_result}")
                        
                        # Step 4: Generate final answer using tool result
                        final_prompt = f"""
User asked: {user_input}

I used the {tool_call['tool_name']} tool and got this result: {tool_result}

Now provide a complete, natural, and helpful final answer to the user's question using this tool result. Be conversational and explain the result clearly.

Final answer:"""

                        final_response = ollama_client.chat(
                            model=model,
                            messages=[{"role": "user", "content": final_prompt}],
                            options=ollama_options
                        )
                        
                        print(f"\n✅ Final Answer: {final_response['message']['content']}")
                        
                    except Exception as tool_error:
                        print(f"❌ Tool execution error: {str(tool_error)}")
                        
                        # Fallback response
                        fallback_prompt = f"User asked: {user_input}\n\nI couldn't use the required tool. Please provide a helpful response explaining this:"
                        
                        fallback_response = ollama_client.chat(
                            model=model,
                            messages=[{"role": "user", "content": fallback_prompt}],
                            options=ollama_options
                        )
                        
                        print(f"\n⚠️ Answer: {fallback_response['message']['content']}")
                        
                else:
                    print("❌ Could not parse tool decision. Providing direct response...")
                    
                    # Fallback to direct response
                    direct_prompt = f"User asked: {user_input}\n\nProvide a helpful answer:"
                    
                    direct_response = ollama_client.chat(
                        model=model,
                        messages=[{"role": "user", "content": direct_prompt}],
                        options=ollama_options
                    )
                    
                    print(f"\n💬 Answer: {direct_response['message']['content']}")
                    
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
