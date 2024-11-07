# Driver AI Monorepo

## Development

To maintain code quality and consistency across our codebase, we use **pre-commit** along with **Ruff** for linting and formatting. Follow the steps below to set up pre-commit and Ruff in your local environment.

### Setting Up Pre-commit Hooks

To ensure code standards are enforced automatically, you’ll need to set up pre-commit hooks on your local machine.

#### 1. Install Pre-commit

You can install pre-commit globally on your system using Python or Homebrew (for macOS users):

- **Using Global System Python**:

  ```bash
  pip install pre-commit
  ```

- **Using Homebrew (macOS)**:

  ```bash
  brew install pre-commit
  ```

#### 2. Install Pre-commit Hooks

Once pre-commit is installed, set up the hooks defined in the repository:

- Navigate to the root of the monorepo.
- Run the following command to install the hooks:

  ```bash
  pre-commit install
  ```

This command installs the pre-commit hooks as defined in the `.pre-commit-config.yaml` file. These hooks will automatically run Ruff and other linters whenever you make a commit, helping maintain code quality and consistency.

### Running Pre-commit Hooks Manually

Normally, pre-commit only examines the files that change in a commit, and runs on each commit.

To run the pre-commit hooks on all files manually:

```bash
pre-commit run --all-files
```

This is helpful to make sure all files in the repository are compliant with the code standards **but it may introduce a lot of changes**, which isn't necessarily desirable to do all at once.
