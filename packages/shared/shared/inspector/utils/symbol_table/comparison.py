"""
Utilities for timing and comparing symbol table approaches.
"""

import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TimingInfo:
    """Timing information for different phases of symbol table construction."""

    parsing_time: float = 0.0
    visibility_time: float = 0.0
    linking_time: float = 0.0
    reification_time: float = 0.0
    total_time: float = 0.0

    def __add__(self, other: "TimingInfo") -> "TimingInfo":
        return TimingInfo(
            parsing_time=self.parsing_time + other.parsing_time,
            visibility_time=self.visibility_time + other.visibility_time,
            linking_time=self.linking_time + other.linking_time,
            reification_time=self.reification_time + other.reification_time,
            total_time=self.total_time + other.total_time,
        )


@dataclass
class ComparisonResult:
    """Result of comparing two visibility maps."""

    are_equal: bool
    total_files: int
    total_dependencies: int
    differences: list[str]
    dfs_timing: TimingInfo
    topological_timing: TimingInfo

    @property
    def speedup_ratio(self) -> float:
        """Calculate speedup ratio (DFS time / Topological time)."""
        if self.topological_timing.visibility_time > 0:
            return (
                self.dfs_timing.visibility_time
                / self.topological_timing.visibility_time
            )
        return 1.0

    @property
    def time_saved(self) -> float:
        """Calculate time saved in seconds."""
        return self.dfs_timing.visibility_time - self.topological_timing.visibility_time


@contextmanager
def timer() -> Generator[dict[str, float], None, None]:
    """Context manager to time execution."""
    timing = {"start": time.time(), "end": 0.0, "elapsed": 0.0}
    try:
        yield timing
    finally:
        timing["end"] = time.time()
        timing["elapsed"] = timing["end"] - timing["start"]


def compare_visibility_maps(
    dfs_map: dict[Path, set[Path]], topological_map: dict[Path, set[Path]]
) -> ComparisonResult:
    """
    Compare two visibility maps for exact equality and generate detailed report.

    Args:
        dfs_map: Visibility map from DFS approach
        topological_map: Visibility map from topological sort approach

    Returns:
        ComparisonResult with detailed comparison information
    """
    differences = []
    total_files = len(dfs_map)
    total_dependencies = sum(len(deps) for deps in dfs_map.values())

    # Check if maps have same keys
    dfs_files = set(dfs_map.keys())
    topo_files = set(topological_map.keys())

    if dfs_files != topo_files:
        missing_in_topo = dfs_files - topo_files
        missing_in_dfs = topo_files - dfs_files

        if missing_in_topo:
            differences.append(
                f"Files missing in topological result: {missing_in_topo}"
            )
        if missing_in_dfs:
            differences.append(f"Files missing in DFS result: {missing_in_dfs}")

    # Compare visibility for each file
    common_files = dfs_files & topo_files
    for file_path in common_files:
        dfs_deps = dfs_map[file_path]
        topo_deps = topological_map[file_path]

        if dfs_deps != topo_deps:
            missing_in_topo = dfs_deps - topo_deps
            missing_in_dfs = topo_deps - dfs_deps

            diff_msg = f"Visibility differences for {file_path}:"
            if missing_in_topo:
                diff_msg += f"\n  - Missing in topological: {missing_in_topo}"
            if missing_in_dfs:
                diff_msg += f"\n  - Missing in DFS: {missing_in_dfs}"

            differences.append(diff_msg)

    are_equal = len(differences) == 0

    return ComparisonResult(
        are_equal=are_equal,
        total_files=total_files,
        total_dependencies=total_dependencies,
        differences=differences,
        dfs_timing=TimingInfo(),  # Will be filled by caller
        topological_timing=TimingInfo(),  # Will be filled by caller
    )


def print_timing_comparison(result: ComparisonResult) -> None:
    """Print a nicely formatted timing comparison."""
    # ANSI color codes
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    CYAN = "\033[96m"

    print(f"\n{BOLD}{BLUE}📊 PERFORMANCE COMPARISON{RESET}")
    print("=" * 50)

    # Timing table
    print(f"\n{BOLD}⏱️  Timing Results:{RESET}")
    print(f"{'Phase':<20} {'DFS (s)':<12} {'Topological (s)':<16} {'Speedup':<10}")
    print("-" * 60)

    def format_speedup(dfs_time: float, topo_time: float) -> str:
        if topo_time > 0:
            speedup = dfs_time / topo_time
            if speedup > 1.2:
                return f"{GREEN}{speedup:.2f}x{RESET}"
            elif speedup < 0.8:
                return f"{RED}{speedup:.2f}x{RESET}"
            else:
                return f"{YELLOW}{speedup:.2f}x{RESET}"
        return "N/A"

    print(
        f"{'Visibility':<20} {result.dfs_timing.visibility_time:<12.3f} "
        f"{result.topological_timing.visibility_time:<16.3f} "
        f"{format_speedup(result.dfs_timing.visibility_time, result.topological_timing.visibility_time)}"
    )

    print(
        f"{'Total':<20} {result.dfs_timing.total_time:<12.3f} "
        f"{result.topological_timing.total_time:<16.3f} "
        f"{format_speedup(result.dfs_timing.total_time, result.topological_timing.total_time)}"
    )

    # Summary stats
    print(f"\n{BOLD}📈 Summary:{RESET}")
    print(f"  • Total files processed: {CYAN}{result.total_files}{RESET}")
    print(f"  • Total dependencies: {CYAN}{result.total_dependencies}{RESET}")
    print(
        f"  • Time saved (visibility): {GREEN if result.time_saved > 0 else RED}{result.time_saved:.3f}s{RESET}"
    )
    if result.speedup_ratio > 1:
        print(f"  • Overall speedup: {GREEN}{result.speedup_ratio:.2f}x faster{RESET}")
    elif result.speedup_ratio < 1:
        print(f"  • Performance: {RED}{1/result.speedup_ratio:.2f}x slower{RESET}")
    else:
        print(f"  • Performance: {YELLOW}Same speed{RESET}")


def print_comparison_result(result: ComparisonResult) -> None:
    """Print a nicely formatted comparison result."""
    # ANSI color codes
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    print(f"\n{BOLD}🔍 PARITY CHECK RESULTS{RESET}")
    print("=" * 50)

    if result.are_equal:
        print(f"{GREEN}✅ PASSED: Both approaches produce identical results{RESET}")
    else:
        print(f"{RED}❌ FAILED: Approaches produce different results{RESET}")
        print(f"\n{BOLD}Differences found:{RESET}")
        for i, diff in enumerate(result.differences, 1):
            print(f"{YELLOW}{i}.{RESET} {diff}")

    print_timing_comparison(result)


def calculate_visibility_stats(visibility_map: dict[Path, set[Path]]) -> dict[str, any]:
    """Calculate statistics about a visibility map."""
    if not visibility_map:
        return {
            "total_files": 0,
            "total_dependencies": 0,
            "avg_dependencies": 0.0,
            "max_dependencies": 0,
            "min_dependencies": 0,
            "files_with_no_deps": 0,
        }

    dep_counts = [len(deps) for deps in visibility_map.values()]

    return {
        "total_files": len(visibility_map),
        "total_dependencies": sum(dep_counts),
        "avg_dependencies": sum(dep_counts) / len(dep_counts),
        "max_dependencies": max(dep_counts),
        "min_dependencies": min(dep_counts),
        "files_with_no_deps": sum(1 for count in dep_counts if count == 1),  # Self only
    }


def print_visibility_stats(
    stats: dict[str, any], title: str = "Visibility Statistics"
) -> None:
    """Print nicely formatted visibility statistics."""
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    print(f"\n{BOLD}{CYAN}📋 {title}{RESET}")
    print("-" * 30)
    print(f"Total files: {stats['total_files']}")
    print(f"Total dependencies: {stats['total_dependencies']}")
    print(f"Average dependencies per file: {stats['avg_dependencies']:.1f}")
    print(f"Max dependencies for a file: {stats['max_dependencies']}")
    print(f"Min dependencies for a file: {stats['min_dependencies']}")
    print(f"Files with no external deps: {stats['files_with_no_deps']}")
