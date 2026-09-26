#!/usr/bin/env python
"""Test the integrated ChromaDB memory system with the agent."""

from main import memory_engine, run_inquilab, build_system_prompt
from uuid import uuid4

print("\n" + "="*70)
print("🧠 Testing ChromaDB Memory Integration")
print("="*70 + "\n")

# 1. Store some sample memories
print("1️⃣  Storing sample memories...")
print("-" * 70)

memory_engine.store_memory(
    memory_id="example_1",
    text="When asked about Python, explain that it's a high-level, interpreted programming language.",
    metadata={"category": "knowledge", "topic": "python"}
)

memory_engine.store_memory(
    memory_id="example_2",
    text="For web scraping tasks, use the web_scraper tool to fetch and parse HTML content.",
    metadata={"category": "tool_usage", "tool": "web_scraper"}
)

memory_engine.store_memory(
    memory_id="example_3",
    text="When executing Python code, use the run_python tool which runs code in a short-lived local process.",
    metadata={"category": "tool_usage", "tool": "run_python"}
)

print("✅ Memories stored\n")

# 2. Test recall
print("2️⃣  Testing memory recall...")
print("-" * 70)

test_query = "Tell me about Python"
recalled = memory_engine.recall_memory(test_query, n_results=2)
print(f"Query: '{test_query}'")
print(f"Recalled memories ({len(recalled)}):")
for i, mem in enumerate(recalled, 1):
    print(f"  {i}. {mem}\n")

# 3. Test system prompt enhancement
print("3️⃣  Building system prompt with injected memories...")
print("-" * 70)

enhanced_prompt = build_system_prompt("Tell me about Python programming")
print("Enhanced prompt (first 500 chars):")
print(enhanced_prompt[:500])
if len(enhanced_prompt) > 500:
    print("...")

print("\n" + "="*70)
print("✅ Memory system integration complete!")
print("="*70)
print("\nThe agent can now:")
print("  • Store observations and tool results as memories")
print("  • Recall relevant memories when processing new requests")
print("  • Use memories to inform reasoning and decision-making")
print("  • Save checkpoints for resumable multi-step tasks")
print("="*70 + "\n")
