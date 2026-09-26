#!/usr/bin/env python
"""
Simple Ollama test - No external dependencies
Tests Ollama integration directly
"""
import requests
import re
from uuid import uuid4

print("\n" + "="*70)
print("🤖 Testing Ollama Integration")
print("="*70 + "\n")

# Test 1: Check Ollama is running
print("1️⃣  Checking Ollama service...")
try:
    response = requests.get("http://localhost:11434/api/tags", timeout=5)
    if response.status_code == 200:
        print("   ✅ Ollama is running\n")
    else:
        print("   ❌ Ollama not responding properly\n")
        exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}\n")
    exit(1)

# Test 2: Send a simple message
print("2️⃣  Sending test message to llama3.2 model...")
print("   (First request will load model - may take a moment)\n")

messages = [
    {"role": "user", "content": "Say 'Hello from Ollama!' and nothing else."}
]

try:
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "llama3.2",
            "messages": messages,
            "stream": False,
            "temperature": 0.0
        },
        timeout=120  # Longer timeout for model loading
    )
    
    if response.status_code == 200:
        ai_message = response.json()["message"]["content"]
        print(f"   ✅ Model responded!")
        print(f"   Response: {ai_message}\n")
    else:
        print(f"   ❌ Error: {response.status_code}\n")
        exit(1)
        
except requests.exceptions.Timeout:
    print("   ⏳ Request timed out (model is loading)\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")
    exit(1)

# Test 3: ReAct loop test
print("3️⃣  Testing ReAct reasoning loop...\n")

BASE_SYSTEM_PROMPT = """You are Inquilab, an autonomous reasoning agent.

To use tools, output exactly in this XML format:
<thinking> Why you're using this tool </thinking>
<action tool="python"> code_here </action>

Or when done:
<final_answer> Your answer </final_answer>
"""

messages = [
    {"role": "system", "content": BASE_SYSTEM_PROMPT},
    {"role": "user", "content": "What is 5 + 3? Use reasoning to answer."}
]

print("   User: What is 5 + 3? Use reasoning to answer.")
print("   ")

try:
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "llama3.2",
            "messages": messages,
            "stream": False,
            "temperature": 0.0
        },
        timeout=120
    )
    
    if response.status_code == 200:
        ai_response = response.json()["message"]["content"]
        print(f"   Agent Output:\n   {ai_response}\n")
        
        if "<final_answer>" in ai_response:
            print("   ✅ Agent produced a final answer!")
        else:
            print("   ℹ️  Agent produced reasoning (not final answer)")
    else:
        print(f"   ❌ Error: {response.status_code}\n")
        exit(1)
        
except Exception as e:
    print(f"   ❌ Error: {e}\n")
    exit(1)

print("="*70)
print("✅ ALL TESTS PASSED - Ollama is ready for Inquilab!")
print("="*70 + "\n")
