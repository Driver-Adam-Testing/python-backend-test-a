from pathlib import Path


def get_prompt_template(f: Path | str) -> str:
    p = Path(f)
    with p.open("r") as pt:
        return pt.read()
