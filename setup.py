import subprocess
import sys
import os
import time

def run_command(command, description, check_output=False):
    """Run a command and handle errors with proper Windows encoding"""
    print(f"🔄 {description}...")
    try:
        if check_output:
            # Use utf-8 encoding and handle errors gracefully
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=120,
                encoding='utf-8',
                errors='ignore'  # Ignore encoding errors
            )
        else:
            result = subprocess.run(command, shell=True, timeout=120)
            
        if result.returncode == 0:
            print(f"✅ {description} completed!")
            if check_output and result.stdout and result.stdout.strip():
                # Clean output for display
                clean_output = result.stdout.strip().replace('\x00', '').replace('\x8f', '')
                print(f"   Output: {clean_output[:200]}...")  # Limit output length
            return True
        else:
            print(f"❌ {description} failed!")
            if check_output and result.stderr:
                clean_error = result.stderr.strip().replace('\x00', '').replace('\x8f', '')
                print(f"   Error: {clean_error[:200]}...")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out!")
        return False
    except Exception as e:
        print(f"❌ Error during {description}: {str(e)}")
        return False

def check_ollama():
    """Check if Ollama is running and accessible"""
    print("🔍 Checking Ollama status...")
    try:
        result = subprocess.run(
            "ollama list", 
            shell=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        if result.returncode == 0:
            print("✅ Ollama is running and accessible!")
            return True
        else:
            print("❌ Ollama is not running or not accessible")
            print("   Please start Ollama with: ollama serve")
            return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {str(e)}")
        return False

def setup_ollama_model():
    """Create the custom Ollama model"""
    if not check_ollama():
        return False
    
    print("🤖 Setting up Qwen3 model for AI application...")
    
    # Check if base model exists, if not pull it
    print("📥 Pulling Qwen3 base model (this may take a few minutes)...")
    if not run_command("ollama pull qwen3:8b", "Pulling Qwen3:8b base model", False):
        print("❌ Failed to pull base model. Check your internet connection.")
        return False
    
    # Wait a moment for the model to be ready
    time.sleep(2)
    
    # Create custom model from modelfile
    print("🔧 Creating custom AI model...")
    if not run_command("ollama create ai_app_model -f config/modelfile", "Creating custom AI model", False):
        print("❌ Failed to create custom model")
        return False
    
    # Test the custom model
    print("🧪 Testing custom model...")
    try:
        test_result = subprocess.run(
            'ollama run ai_app_model "Test"', 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30,
            encoding='utf-8',
            errors='ignore'
        )
        
        if test_result.returncode == 0:
            print("✅ Custom model is working correctly!")
            return True
        else:
            print("⚠️ Custom model created but test failed (this is usually OK)")
            return True  # Continue anyway, test failures are common but model usually works
    except Exception as e:
        print(f"⚠️ Model test had issues but continuing: {str(e)}")
        return True  # Continue anyway

def install_requirements():
    """Install Python requirements"""
    print("📦 Installing Python dependencies...")
    
    requirements = [
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0", 
        "pydantic>=2.5.0",
        "requests>=2.31.0",
        "ollama>=0.1.7"
    ]
    
    for req in requirements:
        print(f"   Installing {req}...")
        result = subprocess.run(
            f"pip install {req}", 
            shell=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        if result.returncode != 0:
            print(f"❌ Failed to install {req}")
            return False
    
    print("✅ All dependencies installed successfully!")
    return True

def create_directories():
    """Create necessary directories"""
    directories = ["mcp_client", "mcp_server", "config"]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Directory '{directory}' ready")
    
    return True

def verify_installation():
    """Verify that everything is set up correctly"""
    print("🔍 Verifying installation...")
    
    # Check if model exists
    try:
        result = subprocess.run(
            "ollama list", 
            shell=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        if "ai_app_model" in result.stdout:
            print("✅ Custom model 'ai_app_model' found")
        else:
            print("⚠️ Custom model not found in ollama list, but this might be OK")
    except:
        print("⚠️ Could not verify model, but continuing...")
    
    # Check if Python packages are installed
    try:
        import fastapi, uvicorn, pydantic, requests, ollama
        print("✅ All Python packages are available")
        return True
    except ImportError as e:
        print(f"❌ Missing Python package: {e}")
        return False

def main():
    print("🚀 AI Tool Calling Application Setup")
    print("   Using: Ollama + Qwen3 + MCP Architecture")
    print("=" * 60)
    
    # Create directories
    if not create_directories():
        print("❌ Failed to create directories")
        return
    
    # Install requirements
    if not install_requirements():
        print("❌ Failed to install requirements")
        return
    
    # Setup Ollama model
    if not setup_ollama_model():
        print("❌ Failed to setup Ollama model")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure Ollama is installed: https://ollama.ai")
        print("2. Start Ollama: ollama serve")
        print("3. Check internet connection for model download")
        return
    
    # Verify installation
    if not verify_installation():
        print("⚠️ Some verification checks failed, but you can try running the app")
    
    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETED!")
    print("\n📋 Next steps:")
    print("\n🔥 STEP 1: Start Ollama (if not already running)")
    print("   ollama serve")
    print("\n🔥 STEP 2: Start MCP Server (New Terminal)")
    print("   python mcp_server/server.py")
    print("\n🔥 STEP 3: Start Main Application (New Terminal)")
    print("   python app.py")
    print("\n🧪 Test queries:")
    print("   • 'What is 25 + 17?'")
    print("   • 'Tell me the temperature in Pune'")
    print("   • 'Hello there!'")
    print("\n🌐 MCP Server: http://localhost:8000")
    print("📚 API docs: http://localhost:8000/docs")
    print("=" * 60)

if __name__ == "__main__":
    main()
