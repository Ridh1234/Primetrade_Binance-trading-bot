#!/usr/bin/env python3
"""
Main entry point for the Binance Futures Trading Bot.

This script provides the proper entry point to avoid import issues
when running the bot from the command line.
"""

import sys
import os

# Add the project root and src directories to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(project_root, 'src')

if project_root not in sys.path:
    sys.path.insert(0, project_root)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Now import and run the CLI
if __name__ == "__main__":
    try:
        from src.cli import main
        main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure you're running from the project root directory")
        print("and that all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
