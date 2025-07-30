#!/usr/bin/env python3
import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import app, init_database

# Initialize database on startup
init_database()

if __name__ == "__main__":
    app.run()

