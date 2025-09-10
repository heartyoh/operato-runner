#!/usr/bin/env python3
"""
Operato Runner - Entry point
Main executable for the Operato Runner application.
"""

import sys
import os
import asyncio

# Add current directory and src to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, current_dir)
sys.path.insert(0, src_dir)

def main():
    """Main entry point for Operato Runner"""
    try:
        # Import and run the main function
        import importlib.util
        spec = importlib.util.spec_from_file_location("main", os.path.join(src_dir, "main.py"))
        main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_module)
        
        # Run the async main function
        asyncio.run(main_module.main())
    except Exception as e:
        print(f"Error running Operato Runner: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()