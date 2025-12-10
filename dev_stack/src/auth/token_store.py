import json
from pathlib import Path

TOKEN_FILE = Path.home() / ".driver_cli.json"


def save_tokens(tokens):
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f)


def load_tokens():
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE) as f:
            return json.load(f)
    return None


def clear_tokens():
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
