from typing import Literal

import modal

app = modal.App("mermaid-syntax-check")

mermaid_image = (
    modal.Image.from_registry("node:20-slim", add_python="3.12")
    .apt_install("chromium", "fonts-dejavu")
    .run_commands(
        "npm install -g @mermaid-js/mermaid-cli",
        'echo \'{"executablePath":"/usr/bin/chromium","args":["--no-sandbox"]}\' > /puppeteer-config.json',
    )
)


@app.function(image=mermaid_image)
def check_mermaid_version() -> None:
    import subprocess

    version = subprocess.check_output(["mmdc", "--version"]).decode().strip()
    print("Mermaid CLI version:", version)


@app.function(image=mermaid_image)
def check_mermaid_syntax(
    code: str,
) -> tuple[Literal["ok", "syntax_error", "other_error"], str]:
    import os
    import subprocess
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".mmd", delete=False) as f_in:
        f_in.write(code)
        f_in.flush()
        in_path = f_in.name

    with tempfile.NamedTemporaryFile("wb", suffix=".svg", delete=False) as f_out:
        out_path = f_out.name

    try:
        subprocess.check_output(
            ["mmdc", "-i", in_path, "-o", out_path, "-p", "/puppeteer-config.json"],
            stderr=subprocess.STDOUT,
        )
        return "ok", ""
    except subprocess.CalledProcessError as e:
        text = e.output.decode("utf-8", errors="replace")
        lower = text.lower()
        if "parse error" in lower or "syntax error" in lower:
            return "syntax_error", text
        return "other_error", text
    finally:
        for path in (in_path, out_path):
            if os.path.exists(path):
                os.remove(path)


@app.local_entrypoint()
def main() -> None:
    check_mermaid_version.remote()

    diagrams = [
        (
            "Simple Valid Graph",
            """
            graph LR
              A --> B
              B --> C
              C --> A
            """,
        ),
        (
            "Broken Arrow",
            """
            graph LR
              A -
            """,
        ),
        (
            "Sequence Diagram OK",
            """
            sequenceDiagram
                Alice->>John: Hello John, how are you?
                John-->>Alice: Great!
            """,
        ),
        (
            "Sequence Diagram Parse Error",
            """
            sequenceDiagram
                Alice->>John Hello
                John->Alice: Missing arrow notation
            """,
        ),
        (
            "State Diagram Valid",
            """
            stateDiagram
                [*] --> State1
                State1 --> State2
                State2 --> [*]
            """,
        ),
        (
            "State Diagram Missing Syntax",
            """
            stateDiagram
                [*] --> Something
                Something --
            """,
        ),
        (
            "Another Graph Missing Node",
            """
            graph TD
               X -->
            """,
        ),
        (
            "Flowchart with Good Syntax",
            """
            flowchart TB
               Start((Start)) --> Decision{Ready?}
               Decision -->|Yes| End((Done))
               Decision -->|No| Start
            """,
        ),
    ]

    RESET = "\033[0m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"

    print("\n=== Mermaid Syntax Check ===\n")
    for title, code in diagrams:
        status, err = check_mermaid_syntax.remote(code)
        if status == "ok":
            color = GREEN
        elif status == "syntax_error":
            color = RED
        else:
            color = YELLOW
        print(f"{title:35} => {color}{status}{RESET}")
        if err:
            for line in err.strip().splitlines():
                print(f"   {line}")
        print()
