"""
This module is used to generate a symbol map from a source file using ctags.

You will need to install universal ctags to use this module!
"""

import subprocess
import tempfile
import os
from pathlib import Path
import json


GREEN = "\033[92m"
RESET = "\033[0m"


def extract_symbols_w_ctags(
    root_rel_path: Path, file_content: str
) -> list[dict[str, any]]:
    with tempfile.NamedTemporaryFile(
        mode="w+", suffix=root_rel_path.suffix, delete=False
    ) as temp_file:
        temp_file.write(file_content)
        temp_file.flush()
        temp_file_name = temp_file.name

    command = ["ctags", "--fields=+ne", "--output-format=json", temp_file_name]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"A subprocess error occurred: {e.stderr}")
        raise
    finally:
        os.remove(temp_file_name)

    output = result.stdout
    return [json.loads(line) for line in output.strip().split("\n") if line]


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Symbol detection CLI")
    parser.add_argument("path", type=Path, help="Path to target source file")
    args = parser.parse_args()
    file_str = args.path.read_text()
    file_lines = file_str.splitlines()
    tags = extract_symbols_w_ctags(args.path, file_str)
    tags.sort(key=lambda tag: tag["line"])
    for tag in tags:
        if tag.get("end"):
            print(f"\n{GREEN}{tag['kind']} (L{tag['line']}-L{tag['end']}){RESET}")
            print(tag)
            snippet = "\n".join(file_lines[tag["line"] - 1 : tag["end"]])
            print(snippet)
        else:
            print(f"\n{GREEN}{tag['kind']} (L{tag['line']}){RESET}")
            print(tag)
            print(file_lines[tag["line"] - 1])
