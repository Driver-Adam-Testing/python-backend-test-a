# Purpose
This Python script is designed to automate the process of running the `poetry lock` command across multiple interdependent Python projects within a directory structure, such as a monorepo. The script ensures that dependencies are locked in the correct order by analyzing the interdependencies between projects. It first checks for the required version of Poetry, then locates all `pyproject.toml` files within the specified root directory. By extracting project names and their dependencies from these files, it constructs a dependency graph. Using this graph, the script determines the correct execution order for running `poetry lock` to prevent errors or inconsistencies that might arise from processing projects out of dependency order.

The script is structured as a command-line tool, utilizing the `argparse` module to handle user inputs such as the root directory to search and a dry-run option to simulate the process without executing commands. Key components include functions for checking the Poetry version, locating `pyproject.toml` files, extracting project information, creating a dependency graph, determining execution order using a topological sort, and executing the `poetry lock` command in the correct sequence. This script is particularly useful for developers managing complex project structures with multiple interdependent components, ensuring consistent dependency management across projects.
# Imports and Dependencies

---
- `argparse`
- `subprocess`
- `sys`
- `graphlib`
- `pathlib`
- `toml`


# Functions

---
### check_poetry_version 
The `check_poetry_version` function verifies that the installed Poetry version is 2.x and exits the program if it is not.
- **Inputs**:
    - None
- **Control Flow**:
    - The function attempts to run the command `poetry --version` using `subprocess.run` to capture the output.
    - It checks if the output contains the string ' 2.' to verify that the Poetry version is 2.x.
    - If the version is not 2.x, it raises a `ValueError` with a message indicating that Poetry version 2.x is required.
    - If a `subprocess.CalledProcessError` is raised during the command execution, it prints an error message and exits the program with a status code of 1.
- **Output**:
    - The function does not return any value; it either completes successfully or exits the program with an error message.


---
### create_dependency_graph 
The `create_dependency_graph` function constructs a dependency graph and a mapping of project names to their directories from a list of pyproject.toml files.
- **Inputs**:
    - `pyproject_files`: A list of Path objects representing the paths to pyproject.toml files.
- **Control Flow**:
    - Initialize two dictionaries: `dependency_graph` for storing project dependencies and `project_name_to_project_dir` for mapping project names to their directories.
    - Iterate over each path in `pyproject_files`.
    - For each path, attempt to extract the project name and its dependencies using the `extract_project_info` function.
    - If successful, store the project directory in `project_name_to_project_dir` and the dependencies in `dependency_graph`.
    - If a KeyError occurs during extraction, print a warning message and continue to the next file.
    - Create a new dictionary `project_name_to_project_deps` that filters dependencies to only include those present in `dependency_graph`.
    - Return the `project_name_to_project_deps` and `project_name_to_project_dir` dictionaries.
- **Output**:
    - A tuple containing two dictionaries: one mapping project names to their dependencies and another mapping project names to their directories.


---
### determine_execution_order 
The function `determine_execution_order` calculates the order in which projects should be executed based on their dependencies using a topological sort.
- **Inputs**:
    - `project_name_to_project_deps`: A dictionary where keys are project names and values are lists of project names that the key project depends on.
- **Control Flow**:
    - Initialize a `TopologicalSorter` with the provided project dependencies.
    - Attempt to generate a static order of projects using `sorter.static_order()`.
    - If a `CycleError` is raised, indicating a circular dependency, print an error message and exit the program with a status code of 1.
- **Output**:
    - A list of project names sorted in an order that respects their dependency constraints, or exits the program if a circular dependency is detected.


---
### execute_poetry_lock 
The `execute_poetry_lock` function runs the 'poetry lock' command in each specified project directory, optionally simulating the action if in dry-run mode, and provides reasons for each action based on project dependencies.
- **Inputs**:
    - `ordered_project_names_and_dirs`: A list of tuples, each containing a project name and its corresponding directory path, ordered by dependency resolution.
    - `project_name_to_project_deps`: A dictionary mapping project names to a list of their local project dependencies.
    - `dry_run`: A boolean flag indicating whether to simulate the 'poetry lock' command without actually executing it.
- **Control Flow**:
    - Iterates over each project name and directory in the provided ordered list.
    - For each project, retrieves its dependencies from the provided dictionary.
    - Constructs a reason text indicating whether the project has dependencies on other local projects.
    - Determines the action text based on the dry_run flag, either 'Would run' or 'Running'.
    - Prints a message indicating the action being taken and the reason for it.
    - If not in dry-run mode, attempts to execute the 'poetry lock' command in the project's directory using subprocess.run.
    - Catches any subprocess.CalledProcessError exceptions, prints an error message, and exits the program with a non-zero status if an error occurs.
- **Output**:
    - The function does not return any value; it performs actions and prints messages to the console.


---
### extract_project_info 
The `extract_project_info` function retrieves the project name and dependencies from a given `pyproject.toml` file.
- **Inputs**:
    - `pyproject_path`: A `Path` object representing the file path to the `pyproject.toml` file.
- **Control Flow**:
    - Load the TOML data from the specified `pyproject.toml` file using `toml.load`.
    - Attempt to retrieve the project name from the nested dictionary structure under `tool.poetry.name`.
    - If the project name is not found, raise a `KeyError` with a specific error message.
    - Attempt to retrieve the dependencies from the nested dictionary structure under `tool.poetry.dependencies`.
    - If the dependencies are not found, raise a `KeyError` with a specific error message.
    - Filter out the 'python' entry from the list of dependencies.
    - Return the project name and the filtered list of dependencies as a tuple.
- **Output**:
    - A tuple containing the project name as a string and a list of dependencies as strings, excluding 'python'.


---
### locate_pyproject_files 
The function `locate_pyproject_files` searches for all 'pyproject.toml' files within a specified root directory and returns their paths.
- **Inputs**:
    - `root_dir`: A string representing the root directory path where the search for 'pyproject.toml' files will begin.
- **Control Flow**:
    - The function uses the `Path` class from the `pathlib` module to create a path object for the given `root_dir`.
    - It then calls the `rglob` method on this path object with the argument 'pyproject.toml', which recursively searches for all files named 'pyproject.toml' within the directory tree starting at `root_dir`.
    - The result of the `rglob` method, which is an iterable of `Path` objects, is converted to a list and returned.
- **Output**:
    - A list of `Path` objects, each representing the path to a 'pyproject.toml' file found within the specified root directory.


---
### main 
The `main` function orchestrates the process of running 'poetry lock' in multiple interdependent Python projects within a directory, ensuring correct dependency order.
- **Inputs**:
    - `None`: The function does not take any direct input parameters but uses command-line arguments.
- **Control Flow**:
    - An argument parser is created to handle command-line arguments for the root directory and dry-run option.
    - The script parses the command-line arguments to determine the root directory and whether to perform a dry run.
    - The `locate_pyproject_files` function is called to find all `pyproject.toml` files in the specified root directory.
    - The `create_dependency_graph` function is invoked to build a dependency graph and map project names to their directories.
    - The `determine_execution_order` function is used to compute the correct order of projects based on their dependencies using topological sorting.
    - A list of tuples containing project names and their directories is created based on the determined execution order.
    - The `execute_poetry_lock` function is called to run 'poetry lock' in each project directory, either executing the command or simulating it based on the dry-run flag.
- **Output**:
    - The function does not return any value; it performs actions based on the command-line arguments and prints output to the console.


