#!/usr/bin/env python
"""
Inquilab Agent - Simplified Version (No ChromaDB)
Autonomous reasoning agent with Ollama and tool execution
"""
import requests
import re
import json
from uuid import uuid4

from sandbox_engine import SecureSandbox
from tools.web_scraper import web_scrape

sandbox = SecureSandbox()

# --- 1. TOOLKIT ---
def web_scraper(url: str) -> str:
    return web_scrape(url)

def run_python(code: str) -> str:
    return sandbox.execute_code(code)

AVAILABLE_TOOLS = {
    "web_scraper": web_scraper,
    "run_python": run_python
}

# --- 2. SYSTEM PROMPT ---
BASE_SYSTEM_PROMPT = """You are Inquilab, an autonomous reasoning agent. 
You must solve the user's request by reasoning step-by-step.
Detect the language of the user's question and answer in that same language.
If the user explicitly requests a different language, answer in the requested language.
Only provide a translation or meaning in another language when the user asks for it.
Keep technical names, URLs, code, and commands unchanged when translating.

You have access to the following tools:
- web_scraper(url: str): Fetches a public web page and returns readable text from it.
- run_python(code: str): Executes Python code in a short-lived local process and returns stdout/stderr.

To use a tool, you MUST output exactly in this XML format:
<thinking> Explain why you are using the tool </thinking>
<action tool="tool_name"> input_string </action>

Wait for the user to provide the "Observation:". 
Once you have the final answer, output:
<final_answer> Your answer here </final_answer>
"""

# --- 3. THE REACT LOOP ---
def run_inquilab(user_prompt: str, session_id: str = None, max_loops: int = 5):
    if session_id is None:
        session_id = str(uuid4())[:8]
    
    print(f"\n🎯 Goal: {user_prompt}")
    print(f"📝 Session: {session_id}\n")
    
    # Initialize messages
    messages = [
        {"role": "system", "content": BASE_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    
    step_count = 0
    for loop_count in range(max_loops):
        print(f"🔄 Loop {loop_count + 1} / {max_loops} - Thinking...")
        
        # 1. Call Ollama
        try:
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "llama3.2",
                    "messages": messages,
                    "stream": False,
                    "temperature": 0.0
                },
                timeout=300  # 5 minutes timeout for large models
            )
            response.raise_for_status()
            ai_message = response.json()["message"]["content"]
        except requests.exceptions.Timeout:
            print("❌ Model request timed out (still thinking)")
            print("   Try again or use a faster model: ollama pull mistral:7b")
            return
        except Exception as e:
            print(f"❌ Error communicating with Ollama: {e}")
            print("   Make sure Ollama is running: python test_ollama.py")
            return
        
        print(f"🤖 Inquilab Output:\n{ai_message}\n")
        messages.append({"role": "assistant", "content": ai_message})
        
        # 2. Check if task is complete
        if "<final_answer>" in ai_message:
            print("✅ Task Complete.")
            
            # Extract final answer
            final_answer_match = re.search(r'<final_answer>(.*?)</final_answer>', ai_message, re.DOTALL)
            if final_answer_match:
                final_answer = final_answer_match.group(1).strip()
                print(f"\n📋 Final Answer:\n{final_answer}\n")
            
            break
        
        # 3. Parse for an Action
        action_match = re.search(r'<action tool="(.*?)">(.*?)</action>', ai_message, re.DOTALL)
        
        if action_match:
            step_count += 1
            tool_name = action_match.group(1).strip()
            tool_input = action_match.group(2).strip()
            
            # 4. Execute the tool
            if tool_name in AVAILABLE_TOOLS:
                print(f"🛠️  Executing tool: {tool_name}")
                observation = AVAILABLE_TOOLS[tool_name](tool_input)
                print(f"👀 Tool returned {len(observation)} characters\n")
            else:
                observation = f"Observation: Error - Tool '{tool_name}' does not exist. Available: {list(AVAILABLE_TOOLS.keys())}"
            
            # Feed observation back to model
            messages.append({"role": "user", "content": observation})
        else:
            # Model forgot to use XML tags
            print("⚠️ No valid action or final answer found. Prompting model to correct syntax.")
            messages.append({"role": "user", "content": "Please output a valid <action> or <final_answer>."})

def main():
    """Run the Inquilab agent."""
    print("\n" + "="*70)
    print("🤖 Inquilab - Autonomous Reasoning Agent")
    print("="*70)
    print("\n✨ Features:")
    print("   • 🌐 Web scraping tool")
    print("   • 🐍 Local Python execution")
    print("   • 🤖 Local LLM reasoning via Ollama")
    print("   • 💬 ReAct reasoning loop")
    print("\n" + "="*70 + "\n")
    
    # Choose your prompt
    prompt = "What is the current time? Use Python to check it."
    # prompt = "Summarize the content of https://example.com"
    # prompt = "Calculate 25 * 40 using Python"
    
    print(f"📝 Running prompt: {prompt}\n")
    run_inquilab(prompt)
    
    print("\n" + "="*70)
    print("✅ Agent completed successfully!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()


