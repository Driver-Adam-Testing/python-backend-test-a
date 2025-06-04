import argparse
from pathlib import Path


def run_and_print_sym_table(project_abspath: Path) -> None:
    from utils.symbol_table import build_symbol_table, print_summary

    files = list(project_abspath.rglob("*"))
    files = [f for f in files if f.is_file()]
    symbol_table = build_symbol_table(files, project_abspath)
    print_summary(symbol_table)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build and display symbol table for a project"
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default="/Users/andrewmark/Downloads/cpp_and_py",
        help="Path to the project directory",
    )
    args = parser.parse_args()

    project_abspath = Path(args.project_path).resolve()
    run_and_print_sym_table(project_abspath)


if __name__ == "__main__":
    main()
