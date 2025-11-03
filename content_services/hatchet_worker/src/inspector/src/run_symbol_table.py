import argparse
from pathlib import Path

from utils.symbol_table.comparison import TimingInfo


def run_and_print_sym_table(
    project_abspath: Path,
    show_timing: bool = True,
) -> None:
    from utils.symbol_table import build_symbol_table, print_summary

    files = list(project_abspath.rglob("*"))
    files = [f for f in files if f.is_file()]

    print("Building symbol table...")

    if show_timing:
        symbol_table, timing = build_symbol_table(
            files, project_abspath, return_timing=True
        )
        print_timing_info(timing)
    else:
        symbol_table = build_symbol_table(files, project_abspath)

    print_summary(symbol_table)


def print_timing_info(timing: TimingInfo) -> None:
    """Print timing information for a single approach."""
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    print(f"\n{BOLD}{BLUE}⏱️  TIMING RESULTS{RESET}")
    print("-" * 40)
    print(f"Parsing:      {CYAN}{timing.parsing_time:.3f}s{RESET}")
    print(f"Visibility:   {CYAN}{timing.visibility_time:.3f}s{RESET}")
    print(f"Linking:      {CYAN}{timing.linking_time:.3f}s{RESET}")
    print(f"Reification:  {CYAN}{timing.reification_time:.3f}s{RESET}")
    print("-" * 40)
    print(f"Total:        {BOLD}{CYAN}{timing.total_time:.3f}s{RESET}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build and display symbol table for a project"
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default="/Users/shaneghiotto/driver/uploaded_codebases/Avalonia",
        help="Path to the project directory",
    )
    parser.add_argument(
        "--timing",
        action="store_true",
        help="Show detailed timing information",
    )
    args = parser.parse_args()

    project_abspath = Path(args.project_path).resolve()

    run_and_print_sym_table(project_abspath, show_timing=args.timing)


if __name__ == "__main__":
    main()
