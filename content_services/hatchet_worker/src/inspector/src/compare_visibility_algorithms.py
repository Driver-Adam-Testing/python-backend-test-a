import argparse
from collections import defaultdict
from pathlib import Path

from utils.lang_specialization.symbol_common import Lang
from utils.symbol_table.comparison import (
    TimingInfo,
    compare_visibility_maps,
)
from utils.symbol_table.core import (
    ParsedProject,
    ParsedProjectWithVisibility,
    VisibilityAlgorithm,
)
from utils.symbol_table.language_utils import get_language_providers


def run_multi_algorithm_comparison(
    project_abspath: Path, algorithms: list[VisibilityAlgorithm] | None = None
) -> None:
    """Run multiple visibility algorithms and compare results."""

    files = list(project_abspath.rglob("*"))
    files = [f for f in files if f.is_file()]

    if algorithms is None:
        algorithms = list(VisibilityAlgorithm)

    print(f"🔄 Running comparison between {len(algorithms)} algorithms:")
    for algo in algorithms:
        print(f"   - {algo.value}")
    print()

    # Group files by language
    providers = get_language_providers()
    language_groups: dict[str, list[Path]] = defaultdict(list)

    for file_path in files:
        lang = Lang.from_ext(file_path.suffix)
        match lang:
            case Lang.C | Lang.CPP | Lang.C_OR_CPP_HEADER:
                language_groups["c_cpp"].append(file_path)
            case Lang.PYTHON:
                language_groups["python"].append(file_path)
            case Lang.JAVA:
                language_groups["java"].append(file_path)

    # Store results for each algorithm
    all_results: dict[VisibilityAlgorithm, dict[str, any]] = {
        algo: {"visibility_maps": {}, "timings": TimingInfo(), "errors": []}
        for algo in algorithms
    }

    # Process each language group
    for lang, lang_files in language_groups.items():
        if not lang_files:
            continue

        print(f"\n📋 Processing {lang} files ({len(lang_files)} files)...")

        provider = providers[lang]
        parser = provider.get_parser()
        resolver = provider.get_resolver()

        # Parse files once
        print("  📖 Parsing files...")
        parsed = ParsedProject.from_files(
            lang_files,
            project_abspath,
            parser=parser,
            num_workers=8,
        )

        # Run each algorithm
        for algo in algorithms:
            print(f"  🔧 Running {algo.value} algorithm...")
            try:
                visibility_result, timing = (
                    ParsedProjectWithVisibility.from_parsed_project(
                        parsed,
                        resolver=resolver,
                        num_workers=8,
                        algorithm=algo,
                        return_timing=True,
                    )
                )

                # Store results
                all_results[algo]["visibility_maps"][lang] = (
                    visibility_result.visibility_map
                )
                all_results[algo]["timings"] = all_results[algo]["timings"] + timing

            except Exception as e:
                print(f"    ❌ Error: {e}")
                all_results[algo]["errors"].append(f"{lang}: {e!s}")

    # Compare results
    print("\n" + "=" * 80)
    print("📊 COMPARISON RESULTS")
    print("=" * 80)

    # Use DFS as baseline for comparison
    baseline_algo = VisibilityAlgorithm.DFS
    baseline_results = all_results[baseline_algo]

    print(f"\n🎯 Using {baseline_algo.value} as baseline for comparison")

    # Compare each algorithm against baseline
    for algo in algorithms:
        if algo == baseline_algo:
            continue

        print(f"\n📌 Comparing {algo.value} vs {baseline_algo.value}:")

        if all_results[algo]["errors"]:
            print("  ⚠️  Errors encountered:")
            for error in all_results[algo]["errors"]:
                print(f"     - {error}")
            continue

        # Compare visibility maps for each language
        all_equal = True
        for lang in all_results[algo]["visibility_maps"]:
            if lang not in baseline_results["visibility_maps"]:
                continue

            algo_map = all_results[algo]["visibility_maps"][lang]
            baseline_map = baseline_results["visibility_maps"][lang]

            comparison = compare_visibility_maps(baseline_map, algo_map)

            if not comparison.are_equal:
                all_equal = False
                print(f"  ❌ {lang}: Results differ!")
                print(f"     Files with differences: {len(comparison.differences)}")
                for diff in comparison.differences[:3]:  # Show first 3
                    print(f"     - {diff}")
                if len(comparison.differences) > 3:
                    print(f"     ... and {len(comparison.differences) - 3} more")
            else:
                print(f"  ✅ {lang}: Results match ({comparison.total_files} files)")

        if all_equal:
            print("  ✅ Overall: All results match baseline!")

    # Print timing comparison
    print("\n" + "=" * 80)
    print("⏱️  PERFORMANCE COMPARISON")
    print("=" * 80)

    # Sort algorithms by total time
    timing_data = [
        (algo, all_results[algo]["timings"].visibility_time)
        for algo in algorithms
        if not all_results[algo]["errors"]
    ]
    timing_data.sort(key=lambda x: x[1])

    print("\nVisibility computation times:")
    print("-" * 40)

    baseline_time = all_results[baseline_algo]["timings"].visibility_time

    for algo, vis_time in timing_data:
        speedup = baseline_time / vis_time if vis_time > 0 else float("inf")
        marker = "📍" if algo == baseline_algo else "  "
        print(
            f"{marker} {algo.value:15} {vis_time:8.3f}s  ({speedup:5.2f}x vs {baseline_algo.value})"
        )

    # Print detailed statistics
    print("\n📈 Algorithm Statistics:")
    print("-" * 40)

    for algo in algorithms:
        if all_results[algo]["errors"]:
            continue

        total_files = sum(
            len(vm) for vm in all_results[algo]["visibility_maps"].values()
        )
        total_deps = sum(
            sum(len(deps) for deps in vm.values())
            for vm in all_results[algo]["visibility_maps"].values()
        )

        print(f"\n{algo.value}:")
        print(f"  Files processed: {total_files}")
        print(f"  Total dependencies: {total_deps}")
        print(f"  Avg deps per file: {total_deps/total_files:.1f}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare visibility algorithms for symbol table construction"
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default="/Users/andrewmark/Downloads/chesslib7",
        help="Path to the project directory",
    )
    parser.add_argument(
        "--algorithms",
        nargs="+",
        choices=[algo.value for algo in VisibilityAlgorithm],
        help="Specific algorithms to compare (default: all)",
    )
    args = parser.parse_args()

    project_abspath = Path(args.project_path).resolve()

    algorithms = None
    if args.algorithms:
        algorithms = [VisibilityAlgorithm(algo) for algo in args.algorithms]

    run_multi_algorithm_comparison(project_abspath, algorithms)


if __name__ == "__main__":
    main()
