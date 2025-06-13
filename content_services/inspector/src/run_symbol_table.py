import argparse
from pathlib import Path

from utils.symbol_table.comparison import TimingInfo
from utils.symbol_table.core import VisibilityAlgorithm


def run_and_print_sym_table(
    project_abspath: Path,
    algorithm: VisibilityAlgorithm = VisibilityAlgorithm.SCC,
    show_timing: bool = True,
) -> None:
    from utils.symbol_table import build_symbol_table, print_summary

    files = list(project_abspath.rglob("*"))
    files = [f for f in files if f.is_file()]

    print(f"Building symbol table using {algorithm.value} visibility algorithm...")

    if show_timing:
        symbol_table, timing = build_symbol_table(
            files, project_abspath, algorithm=algorithm, return_timing=True
        )
        print_timing_info(timing, algorithm.value)
    else:
        symbol_table = build_symbol_table(files, project_abspath, algorithm=algorithm)

    print_summary(symbol_table)


def print_timing_info(timing: TimingInfo, algorithm: str) -> None:
    """Print timing information for a single approach."""
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    print(f"\n{BOLD}{BLUE}⏱️  {algorithm.upper()} TIMING RESULTS{RESET}")
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
        default="/Users/andrewmark/Downloads/chesslib7",
        help="Path to the project directory",
    )
    parser.add_argument(
        "--algorithm",
        type=str,
        choices=[algo.value for algo in VisibilityAlgorithm],
        default=VisibilityAlgorithm.SCC.value,
        help="Visibility algorithm to use (default: scc)",
    )
    parser.add_argument(
        "--timing",
        action="store_true",
        help="Show detailed timing information",
    )
    args = parser.parse_args()

    project_abspath = Path(args.project_path).resolve()
    algorithm = VisibilityAlgorithm(args.algorithm)

    run_and_print_sym_table(
        project_abspath, algorithm=algorithm, show_timing=args.timing
    )


if __name__ == "__main__":
    main()
