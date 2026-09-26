#!/usr/bin/env python
"""
Ollama Setup & Diagnostic Tool
Helps install, configure, and verify Ollama connection
"""
import sys
import platform
import subprocess
from ollama_connector import OllamaConnector

def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def print_step(number, title):
    """Print a step header."""
    print(f"\n📋 Step {number}: {title}")
    print("-" * 70)

def check_ollama_installed():
    """Check if Ollama is installed."""
    print_step(1, "Checking if Ollama is installed")
    
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ Ollama is installed")
            print(f"   Version: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"⚠️  Error checking Ollama: {e}")
    
    print("❌ Ollama is not installed or not in PATH")
    return False

def suggest_ollama_installation():
    """Suggest how to install Ollama."""
    print_step(2, "Installation Instructions")
    
    system = platform.system()
    
    print(f"Your OS: {system}\n")
    
    if system == "Windows":
        print("📥 Windows Installation:")
        print("   1. Download from: https://ollama.ai/download/windows")
        print("   2. Run the installer (Ollama-windows-amd64.exe)")
        print("   3. Follow the installation prompts")
        print("   4. Restart your terminal after installation")
    
    elif system == "Darwin":  # macOS
        print("📥 macOS Installation:")
        print("   1. Download from: https://ollama.ai/download/mac")
        print("   2. Run the installer")
        print("   3. Or use Homebrew: brew install ollama")
    
    elif system == "Linux":
        print("📥 Linux Installation:")
        print("   Run: curl https://ollama.ai/install.sh | sh")
    
    print("\n   After installation, Ollama will run as a service.")
    print("   It will be available at http://localhost:11434")

def check_ollama_running():
    """Check if Ollama service is running."""
    print_step(3, "Checking if Ollama is running")
    
    ollama = OllamaConnector()
    
    if ollama.verify_connection():
        print("✅ Ollama is running and responding")
        status = ollama.get_status()
        print(f"   URL: {status['base_url']}")
        return True
    else:
        print("❌ Ollama is not running")
        print("\n   To start Ollama:")
        print("   - On Windows: It should auto-start after installation")
        print("   - On macOS/Linux: Run 'ollama serve' in terminal")
        return False

def check_models():
    """Check what models are available."""
    print_step(4, "Checking available models")
    
    ollama = OllamaConnector()
    
    if not ollama.verify_connection():
        print("⚠️  Cannot connect to Ollama to check models")
        return []
    
    models = ollama.get_available_models()
    
    if models:
        print(f"✅ Found {len(models)} model(s):")
        for model in models:
            print(f"   • {model}")
        return models
    else:
        print("❌ No models installed")
        return []

def pull_default_model():
    """Pull default model (llama3.2)."""
    print_step(5, "Setting up default model")
    
    ollama = OllamaConnector()
    
    if not ollama.verify_connection():
        print("⚠️  Cannot connect to Ollama to pull model")
        print("   Start Ollama first and try again")
        return False
    
    default_model = "llama3.2"
    available_models = ollama.get_available_models()
    
    if default_model in available_models:
        print(f"✅ Model '{default_model}' is already installed")
        return True
    
    print(f"📥 Model '{default_model}' not found")
    print(f"\nAvailable lightweight models to try:")
    print(f"   • llama2:7b      (3.8 GB) - Fast, good for basic tasks")
    print(f"   • mistral:7b     (4.0 GB) - Fast reasoning")
    print(f"   • neural-chat:7b (4.8 GB) - Good quality")
    print(f"   • qwen2.5:7b     (3.8 GB) - Fast, multilingual")
    print(f"\nTo pull a model, run:")
    print(f"   ollama pull llama3.2")
    print(f"   ollama pull mistral:7b")
    print(f"   etc...")
    
    return False

def test_ollama_connection():
    """Test a simple call to Ollama."""
    print_step(6, "Testing model connection")
    
    ollama = OllamaConnector()
    
    if not ollama.verify_connection():
        print("⚠️  Ollama not running, skipping test")
        return False
    
    print("🧪 Sending test message to Ollama model...")
    print(f"   Small loading model: {ollama.small_model}")
    print(f"   Large working model: {ollama.large_model}")
    
    response = ollama.chat([
        {"role": "user", "content": "Say 'Hello from Ollama' and nothing else"}
    ])
    
    if response:
        print(f"✅ Model responded successfully!")
        print(f"\n   Response: {response[:200]}")
        return True
    else:
        print("❌ Model did not respond")
        return False

def show_configuration():
    """Show current configuration."""
    print_step(7, "Current Configuration")
    
    ollama = OllamaConnector()
    status = ollama.get_status()
    
    print("Ollama Configuration:")
    print(f"  Host:              {status['host']}")
    print(f"  Port:              {status['port']}")
    print(f"  Base URL:          {status['base_url']}")
    print(f"  Small loading model: {status['small_model']}")
    print(f"  Large working model: {status['large_model']}")
    print(f"  Connected:         {'✅ Yes' if status['connected'] else '❌ No'}")
    
    print("\nEnvironment Variables:")
    print("  You can customize with these env vars:")
    print("  • OLLAMA_HOST    - Ollama host (default: localhost)")
    print("  • OLLAMA_PORT    - Ollama port (default: 11434)")
    print("  • OLLAMA_SMALL_MODEL - Small model loaded first (default: tinyllama)")
    print("  • OLLAMA_LARGE_MODEL - Large model used for work (default: llama3.2:latest)")

def main():
    """Run diagnostic checks."""
    print_header("🚀 Ollama Setup & Diagnostic Tool")
    
    print("This tool will help you:")
    print("  1. Check if Ollama is installed")
    print("  2. Verify Ollama is running")
    print("  3. Check available models")
    print("  4. Test connection to the LLM")
    
    # Run checks
    installed = check_ollama_installed()
    
    if not installed:
        suggest_ollama_installation()
        print("\n" + "="*70)
        print("❌ Please install Ollama first, then run this script again")
        print("="*70 + "\n")
        sys.exit(1)
    
    running = check_ollama_running()
    
    if not running:
        print("\n" + "="*70)
        print("⚠️  Ollama is installed but not running")
        print("="*70)
        system = platform.system()
        if system == "Windows":
            print("   The Ollama service should auto-start after installation.")
            print("   Check System Tray or try restarting Windows.")
        elif system == "Darwin":
            print("   The Ollama service should auto-start after installation.")
            print("   If not, open Ollama.app from Applications.")
        else:  # Linux
            print("   Start Ollama with: ollama serve")
        print("="*70 + "\n")
        sys.exit(1)
    
    models = check_models()
    
    if not models:
        print("\n" + "="*70)
        print("⚠️  No models installed yet")
        print("="*70 + "\n")
        pull_default_model()
        sys.exit(1)
    
    test_ollama_connection()
    show_configuration()
    
    print_header("✅ Setup Complete!")
    print("Your Ollama connection is ready to use with Inquilab!")
    print("\nNext steps:")
    print("  1. Run: python agent.py")
    print("  2. Or run: python main.py")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
