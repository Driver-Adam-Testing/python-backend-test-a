## Folders
- **[integrations](driver_data/integrations.driver.md)**: The `integrations` folder in the `python-backend` codebase contains configuration files for setting up and deploying a GitLab Enterprise Edition service using Docker.

## Files
- **[__init__.py](driver_data/__init__.py.driver.md)**: Empty file (no analyzable contents).
- **[associate_codebases_gh_repo_ids.py](driver_data/associate_codebases_gh_repo_ids.py.driver.md)**: The `associate_codebases_gh_repo_ids.py` file contains a script that associates existing codebases with GitHub repository IDs by matching them with GitHub Installation IDs, with an option for a dry run to simulate the process without making database changes.
- **[copy_data.py](driver_data/copy_data.py.driver.md)**: The `copy_data.py` file in the `python-backend` codebase provides functionality to migrate codebase data, including database records and S3 files, from a source to a destination environment, with options to skip certain steps.
- **[migrate_gh_app_ids.py](driver_data/migrate_gh_app_ids.py.driver.md)**: The `migrate_gh_app_ids.py` file in the `python-backend` codebase is a script that migrates GitHub App installation IDs from AWS Secrets Manager to a database, with support for dry-run mode to simulate the migration process.
- **[poetry.lock](driver_data/poetry.lock.driver.md)**: The `poetry.lock` file in the `python-backend` codebase specifies the exact versions and dependencies of packages used in the project, ensuring consistent environments across different installations.
- **[pyproject.toml](driver_data/pyproject.toml.driver.md)**: The `pyproject.toml` file in the `python-backend` codebase specifies the project metadata, dependencies, and build system configuration for the `driver_data` package using Poetry.
- **[README.md](driver_data/README.md.driver.md)**: The `README.md` file in the `python-backend/driver_data` directory provides instructions for copying database and S3 records for a specific organization and codebase ID to a local destination, including example commands and environment configuration details.
