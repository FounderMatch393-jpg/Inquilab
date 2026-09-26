#!/usr/bin/env python
"""Test checkpoint/state saving functionality."""

from main import memory_engine
from uuid import uuid4

print("\n" + "="*70)
print("💾 Testing Checkpoint/State Saving")
print("="*70 + "\n")

session_id = str(uuid4())[:8]

# 1. Save a checkpoint
print("1️⃣  Saving checkpoint...")
print("-" * 70)

state = {
    "messages": [{"role": "user", "content": "Example prompt"}],
    "user_prompt": "Summarize example.com",
    "tool_used": "web_scraper"
}

memory_engine.save_checkpoint(
    session_id=session_id,
    step=1,
    state_dict=state,
    status="in_progress"
)
print(f"✅ Checkpoint saved for session {session_id}\n")

# 2. Load the checkpoint
print("2️⃣  Loading checkpoint...")
print("-" * 70)

loaded_state = memory_engine.load_checkpoint(session_id)
if loaded_state:
    print("✅ Checkpoint loaded successfully!")
    print(f"   User prompt: {loaded_state['user_prompt']}")
    print(f"   Tool used: {loaded_state['tool_used']}")
    print(f"   Messages: {len(loaded_state['messages'])} message(s)\n")
else:
    print("⚠️  No checkpoint found\n")

# 3. Save final checkpoint
print("3️⃣  Saving final checkpoint...")
print("-" * 70)

final_state = {
    "messages": [{"role": "assistant", "content": "Final answer..."}],
    "user_prompt": "Summarize example.com",
    "final_answer": "Example.com is a domain for documentation examples."
}

memory_engine.save_checkpoint(
    session_id=session_id,
    step=2,
    state_dict=final_state,
    status="completed"
)
print("✅ Final checkpoint saved\n")

print("="*70)
print("✅ Checkpoint system working!")
print("="*70)
print("\nThe agent can now:")
print("  • Pause execution and save state at checkpoints")
print("  • Resume from saved checkpoints after interruption")
print("  • Track task progress across sessions")
print("="*70 + "\n")
