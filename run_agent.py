#!/usr/bin/env python
"""Safe runner for the Inquilab agent with proper encoding handling."""
import sys
import os

# Force UTF-8 encoding on Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

# Import and run the agent
from main import run_inquilab

if __name__ == "__main__":
    # Example usage - replace with your actual prompt
    run_inquilab("What is the current time? You can use Python to check it.")
