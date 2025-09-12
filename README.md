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

## Testing CDK Additions in Develop

Since we do not have completely automated infra yet (Modal + Scalegrid being the primary culprits) we cannot create arbitrary environments during development to test our changes against. However, some testing of additional infrastructure and other changes is required, so a `test-in-dev` CDK stack was added to help facilitate testing of _additions_ to the infrastructure. This stack is not automatically deployed anywhere and is entirely manual. Other arbitrary stacks can also be made if desired, for example per-developer (which would be the goal once all other infra creation is automated).

To use the `test-in-dev` stack, make the desired changes in (the `test_in_dev_stack.py` file)[./cdk/test_in_dev_stack.py] and use the `DEPLOYMENT_ENVIRONMENT=test-in-dev cdk deploy` command to publish them.

The mapping from the environment var `DEPLOYMENT_ENVIRONMENT` into different stacks is managed in the `./cdk_app.py` file with a naive set of `if/else` statements and can be customized with new test environments or configurations of existing ones as deemed appropriate.

Other Notes from AWS:

> Model with constructs, deploy with stacks
>
> Stacks are the unit of deployment: everything in a stack is deployed together. So when building your application's higher-level logical units from multiple AWS resources, represent each logical unit as a Construct, not as a Stack. Use stacks only to describe how your constructs should be composed and connected for your various deployment scenarios.
>
> For example, if one of your logical units is a website, the constructs that make it up (such as an Amazon S3 bucket, API Gateway, Lambda functions, or Amazon RDS tables) should be composed into a single high-level construct. Then that construct should be instantiated in one or more stacks for deployment.
>
> By using constructs for building and stacks for deploying, you improve reuse potential of your infrastructure and give yourself more flexibility in how it's deployed.
