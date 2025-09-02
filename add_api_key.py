#!/usr/bin/env python3
import json
import secrets
import os
import stat
from dotenv import load_dotenv

load_dotenv()
API_KEYS_PATH = os.environ.get('API_KEYS_PATH')

def ensure_file():
    """Create the file if it does not exist with correct permissions."""
    if not os.path.exists(API_KEYS_FILE):
        os.makedirs(os.path.dirname(API_KEYS_FILE), exist_ok=True)
        with open(API_KEYS_FILE, "w") as f:
            json.dump({}, f)
        # Set permissions: owner=root rw, group=www-data r
        os.chown(API_KEYS_FILE, 0, 33)  # 0=root, 33=www-data
        os.chmod(API_KEYS_FILE, 0o640)

def load_keys():
    """Load existing API keys from the JSON file."""
    ensure_file()
    with open(API_KEYS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_keys(keys):
    """Save API keys back to the JSON file safely."""
    with open(API_KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=4)
    # Ensure permissions remain correct
    os.chown(API_KEYS_FILE, 0, 33)  # root:www-data
    os.chmod(API_KEYS_FILE, 0o640)

def add_api_key(name: str):
    """Generate a new key for a given user and save it."""
    keys = load_keys()
    key = secrets.token_hex(32)
    keys[name] = key
    save_keys(keys)
    print(f"API key for {name}: {key}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Add a new API key")
    parser.add_argument("name", help="Name of the user for this API key")
    args = parser.parse_args()

    add_api_key(args.name)
