import argparse
import toml
from pathlib import Path
import subprocess
from graphlib import TopologicalSorter, CycleError
import sys


def locate_pyproject_files(root_dir: str) -> list[Path]:
    return list(Path(root_dir).rglob("pyproject.toml"))


def extract_project_info(pyproject_path: Path) -> tuple[str, list[str]]:
    data = toml.load(pyproject_path)
    project_name = (
        data.get("tool", {}).get("poetry", {}).get("name", pyproject_path.parent.name)
    )
    dependencies = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
    dependencies = [dep for dep in dependencies if dep.lower() != "python"]
    return project_name, dependencies


def create_dependency_graph(
    pyproject_files: list[Path],
) -> tuple[dict[str, list[str]], dict[str, Path]]:
    dependency_graph = {}
    project_directories = {}

    for pyproject_path in pyproject_files:
        project_name, dependencies = extract_project_info(pyproject_path)
        project_directories[project_name] = pyproject_path.parent
        dependency_graph[project_name] = dependencies

    for project in dependency_graph:
        dependency_graph[project] = [
            dep for dep in dependency_graph[project] if dep in dependency_graph
        ]

    return dependency_graph, project_directories


def determine_execution_order(dependency_graph: dict[str, list[str]]) -> list[str]:
    sorter = TopologicalSorter(dependency_graph)
    try:
        return list(sorter.static_order())
    except CycleError as error:
        print(f"Error: Circular dependency detected: {error}")
        sys.exit(1)


def execute_poetry_lock(
    project_dirs: list[Path], dependency_graph: dict[str, list[str]], dry_run: bool
) -> None:
    """Execute 'poetry lock --no-update' in each project directory, showing reasons for each action."""
    for project_dir in project_dirs:
        project_name = project_dir.name
        reasons = dependency_graph.get(project_name, [])
        reasons_text = (
            f"depends on local projects: {', '.join(reasons)}"
            if reasons
            else "has no dependencies on other local projects"
        )
        action_text = "Would run" if dry_run else "Running"
        print(
            f"{action_text} 'poetry lock --no-update' in `{project_dir}` because it {reasons_text}"
        )

        if not dry_run:
            try:
                subprocess.run(
                    ["poetry", "lock", "--no-update"], cwd=project_dir, check=True
                )
            except subprocess.CalledProcessError as e:
                print(
                    f"Error: Failed to run 'poetry lock --no-update' in `{project_dir}`. Error: {e}"
                )
                sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="""
        This script automates the process of running 'poetry lock --no-update' in multiple interdependent Python projects
        within a directory structure, such as in a monorepo.

        Motivation:
        When working in a monorepo, managing dependencies
        consistently across projects can be challenging, especially when these projects have interdependencies.
        For example, consider the following scenario:

        - You have four projects: A, B, C, and D.
        - Project A depends on Project B.
        - Project C depends on Project A.
        - Project D has no dependencies on the other projects.

        In this scenario, running 'poetry lock' directly in each project without considering dependencies may cause errors
        or inconsistent lock files, especially if Project A is processed before Project B. This script solves that problem
        by determining the correct order to lock dependencies based on their inter-project dependencies, ensuring that all
        prerequisite dependencies are handled first.

        Example Usage:
        - To run the script on a directory of projects:
            python script.py --root-dir /path/to/projects

        - To perform a dry run and see the plan:
            python script.py --root-dir /path/to/projects --dry-run
        """
    )

    parser.add_argument(
        "--root-dir",
        default=".",
        help="Root directory to search for pyproject.toml files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without executing commands.",
    )
    args = parser.parse_args()

    pyproject_files = locate_pyproject_files(args.root_dir)
    dependency_graph, project_directories = create_dependency_graph(pyproject_files)
    execution_order = determine_execution_order(dependency_graph)

    project_dirs = [
        project_directories[project]
        for project in execution_order
        if project in project_directories
    ]
    execute_poetry_lock(project_dirs, dependency_graph, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
