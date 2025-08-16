#!/usr/bin/env python3
"""
Startup script for running both MCP and HTTP API servers.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gmail_llm.server_launcher import main

if __name__ == "__main__":
    main()