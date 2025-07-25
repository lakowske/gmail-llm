#!/usr/bin/env python3
"""
New Gmail connector script using modular architecture.
This is the main entry point that uses the refactored modules.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gmail_llm.main import main

if __name__ == '__main__':
    main()