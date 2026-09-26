#!/usr/bin/env python
"""
Inquilab Agent - Main Entry Point
Autonomous reasoning agent with memory and local code execution
"""
import sys
import os

# Force UTF-8 encoding on Windows to prevent subprocess encoding issues
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

from main import run_inquilab

def main():
    """Run the Inquilab agent with a user prompt."""
    print("\n" + "="*70)
    print("🤖 Inquilab - Autonomous Reasoning Agent")
    print("="*70)
    print("\n✨ Features:")
    print("   • 🌐 Web scraping tool")
    print("   • 🐍 Local Python execution")
    print("   • 🧠 Memory persistence with SQLite")
    print("   • 💾 Checkpoint system for multi-step tasks")
    print("   • 🤖 Local LLM reasoning via Ollama")
    print("\n" + "="*70 + "\n")
    
    # Example prompts - uncomment the one you want to use
    
    # Simple time check
    prompt = "What is the current time? Use Python to check it."
    
    # Web scraping
    # prompt = "Summarize the content of https://example.com"
    
    # Complex multi-step
    # prompt = "Fetch https://example.com and tell me how many words it has"
    
    print(f"📝 Running prompt: {prompt}\n")
    run_inquilab(prompt)
    
    print("\n" + "="*70)
    print("✅ Agent completed successfully!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
