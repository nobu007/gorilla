"""
pytest configuration for loading environment variables from .env file.
"""

import os
from pathlib import Path

# Find .env file by going up the directory tree
def find_dotenv():
    current_dir = Path(__file__).parent
    while current_dir != current_dir.parent:
        env_file = current_dir / ".env"
        if env_file.exists():
            return env_file
        current_dir = current_dir.parent
    return None

# Load .env file if it exists
env_file = find_dotenv()
if env_file:
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print(f"✅ Loaded .env from {env_file}")
    except ImportError:
        print("⚠️ python-dotenv not available, .env file not loaded")
    except Exception as e:
        print(f"⚠️ Error loading .env file: {e}")
else:
    print("⚠️ No .env file found")