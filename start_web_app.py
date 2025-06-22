"""
Complete web application starter
"""
import subprocess
import sys
import time
import os
from threading import Thread

def check_ollama():
    """Check if Ollama is running"""
    try:
        result = subprocess.run("ollama list", shell=True, capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def start_mcp_server():
    """Start MCP server in background"""
    print("🚀 Starting MCP Server...")
    os.chdir("mcp_server")
    try:
        subprocess.run([sys.executable, "server.py"])
    except KeyboardInterrupt:
        pass

def main():
    print("🌐 AI Web Interface Starter")
    print("=" * 50)
    
    # Check Ollama
    if not check_ollama():
        print("❌ Ollama is not running!")
        print("Please start Ollama first: ollama serve")
        return
    
    print("✅ Ollama is running")
    
    # Start MCP server in background
    print("🔧 Starting MCP Server in background...")
    server_thread = Thread(target=start_mcp_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(3)
    
    # Start web application
    print("🌐 Starting web interface...")
    print("Will be available at: http://localhost:5000")
    print("=" * 50)
    
    try:
        subprocess.run([sys.executable, "web_app.py"])
    except KeyboardInterrupt:
        print("\n👋 Web application stopped")

if __name__ == "__main__":
    main()
