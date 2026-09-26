#!/usr/bin/env python
"""Quick integration test for local Python execution and web scraping tools."""

from main import AVAILABLE_TOOLS

print("\n" + "="*60)
print("Testing Agent Toolkit Integration")
print("="*60 + "\n")

# Test 1: run_python tool
print("1️⃣  Testing run_python tool:")
print("-" * 60)
python_code = """
result = 42
print(f'Calculation result: {result}')
for i in range(3):
    print(f'  Iteration {i}')
"""
response = AVAILABLE_TOOLS['run_python'](python_code)
print(response)

print("\n" + "="*60 + "\n")

# Test 2: web_scraper tool
print("2️⃣  Testing web_scraper tool:")
print("-" * 60)
response = AVAILABLE_TOOLS['web_scraper']('https://example.com')
print(response[:300] + "..." if len(response) > 300 else response)

print("\n" + "="*60)
print("✅ Toolkit integration complete!")
print("="*60 + "\n")
