import requests
import re
import json
import os
import shutil
import subprocess
import sys
import time
from uuid import uuid4

if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

from sandbox_engine import SecureSandbox
from tools.web_scraper import web_scrape

from memory_engine_simple import InquilabStateEngine

from ollama_connector import OllamaConnector

sandbox = SecureSandbox()
memory_engine = InquilabStateEngine()
ollama_client = OllamaConnector()

# --- 1. TOOLKIT ---
def web_scraper(url: str) -> str:
    return web_scrape(url)


def run_python(code: str) -> str:
    return sandbox.execute_code(code)

AVAILABLE_TOOLS = {
    "web_scraper": web_scraper,
    "run_python": run_python
}

# --- 2. SYSTEM ARCHITECTURE (THE PROMPT) ---
BASE_SYSTEM_PROMPT = """You are Inquilab, an autonomous reasoning agent. 
You must solve the user's request by reasoning step-by-step.
Detect the language of the user's question and answer in that same language.
If the user explicitly requests a different language, answer in the requested language.
Only provide a translation or meaning in another language when the user asks for it.
Keep technical names, URLs, code, and commands unchanged when translating.

You have access to the following tools:
- web_scraper(url: str): Fetches a public web page and returns readable text from it.
- run_python(code: str): Executes Python code in a short-lived local process and returns stdout/stderr.

Respond to the current user message immediately. Do not wait for an Observation unless you have first emitted a tool action.
To use a tool, output exactly in this XML format:
<thinking> Explain why you are using the tool </thinking>
<action tool="tool_name"> input_string </action>

After a tool result is provided, continue solving the request. Once you have the final answer, output:
<final_answer> Your answer here </final_answer>
"""

def ensure_ollama_running() -> bool:
    """Try to start Ollama automatically when the user runs the app directly."""
    if ollama_client.verify_connection():
        ollama_client.warm_up()
        return True

    candidates = []
    cli_path = shutil.which("ollama")
    if cli_path:
        candidates.append(cli_path)

    default_windows_path = os.path.join(os.environ.get("USERPROFILE", r"C:\Users\Default"), "AppData", "Local", "Programs", "Ollama", "ollama.exe")
    candidates.append(default_windows_path)

    for candidate in candidates:
        if not candidate or not os.path.exists(candidate):
            continue
        try:
            subprocess.Popen(
                [candidate, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                close_fds=True,
            )
            print("▶️ Attempting to start Ollama in the background...")
            for _ in range(30):
                if ollama_client.verify_connection():
                    ollama_client.warm_up()
                    return True
                time.sleep(1)
        except Exception as exc:
            print(f"⚠️ Could not launch Ollama automatically: {exc}")

    print("❌ Ollama is not running and could not be started automatically.")
    print("   Please run: ollama serve")
    return False

def build_system_prompt(user_query: str) -> str:
    """Build system prompt with injected relevant memories from ChromaDB."""
    memories = memory_engine.recall_memory(user_query, n_results=3)
    
    prompt = BASE_SYSTEM_PROMPT
    if memories:
        prompt += "\n\n--- RELEVANT PAST KNOWLEDGE ---\n"
        for i, memory in enumerate(memories, 1):
            prompt += f"{i}. {memory}\n"
    
    return prompt

# --- 3. THE REACT LOOP ---
def run_inquilab(user_prompt: str, session_id: str = None):
    if not ensure_ollama_running():
        print("❌ Cannot continue because Ollama is unavailable.")
        return None

    if session_id is None:
        session_id = str(uuid4())[:8]
    
    print(f"\n🎯 Goal: {user_prompt}")
    print(f"📝 Session: {session_id}\n")
    
    # Build system prompt with injected memories
    system_prompt = build_system_prompt(user_prompt)
    
    # Initialize the memory array with the system prompt and user goal
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    max_loops = 5
    step_count = 0
    final_answer = None
    last_response = None
    for loop_count in range(max_loops):
        print(f"🔄 Loop {loop_count + 1} / {max_loops} - Thinking...")
        
        # 1. Call the local model via Ollama
        ai_message = ollama_client.chat(messages)
        
        if ai_message is None:
            print("❌ Failed to get response from Ollama")
            return None
            
        print(f"🤖 Inquilab Output:\n{ai_message}\n")
        last_response = ai_message.strip()
        messages.append({"role": "assistant", "content": ai_message})
        
        # 2. Check if the task is complete
        if "<final_answer>" in ai_message:
            print("✅ Task Complete.")
            
            # Extract and store the final answer as a memory
            final_answer_match = re.search(r'<final_answer>(.*?)</final_answer>', ai_message, re.DOTALL)
            if final_answer_match:
                final_answer = final_answer_match.group(1).strip()
                memory_engine.store_memory(
                    memory_id=f"{session_id}_final_answer",
                    text=f"User asked: '{user_prompt}' → Final answer: {final_answer}",
                    metadata={"type": "final_answer", "session": session_id}
                )
            
            # Save final checkpoint
            memory_engine.save_checkpoint(
                session_id=session_id,
                step=step_count + 1,
                state_dict={"messages": messages, "user_prompt": user_prompt},
                status="completed"
            )
            break
            
        # 3. Parse for an Action using Regex
        action_match = re.search(r'<action tool="(.*?)">(.*?)</action>', ai_message, re.DOTALL)
        
        if action_match:
            step_count += 1
            tool_name = action_match.group(1).strip()
            tool_input = action_match.group(2).strip()
            
            # 4. Execute the tool safely
            if tool_name in AVAILABLE_TOOLS:
                observation = AVAILABLE_TOOLS[tool_name](tool_input)
                # Store successful tool usage as memory for future learning
                memory_engine.store_memory(
                    memory_id=f"{session_id}_step_{step_count}_{tool_name}",
                    text=f"Tool '{tool_name}' with input '{tool_input[:100]}' returned: {observation[:500]}",
                    metadata={"tool": tool_name, "session": session_id, "step": step_count}
                )
            else:
                observation = f"Observation: Error - Tool '{tool_name}' does not exist."
                
            print(f"👀 {observation}\n")
            
            # Save checkpoint periodically
            if step_count % 2 == 0:
                memory_engine.save_checkpoint(
                    session_id=session_id,
                    step=step_count,
                    state_dict={"messages": messages, "user_prompt": user_prompt},
                    status="in_progress"
                )
            
            # Feed the observation back to the model for the next loop
            messages.append({"role": "user", "content": observation})
        else:
            # If the model gets confused and forgets to use the XML tags, correct it
            if "<thinking>" not in ai_message and last_response:
                # Accept a direct answer from models that ignore the XML wrapper.
                final_answer = last_response
                break
            print("⚠️ No valid action or final answer found. Prompting model to correct syntax.")
            if loop_count == max_loops - 1:
                # Do not discard a useful answer just because the local model missed the wrapper tag.
                final_answer = last_response
                break
            messages.append({"role": "user", "content": "Please output a valid <action> or <final_answer>."})

    return final_answer

if __name__ == "__main__":
    print("\nInquilab is ready. Ask a question, or press Enter to use the example prompt.")
    user_question = input("\nYou: ").strip()
    if not user_question:
        user_question = "Summarize the homepage content of https://example.com"
    run_inquilab(user_question)


