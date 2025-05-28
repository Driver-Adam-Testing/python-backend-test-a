## Folders
- **[constructs](cdk/constructs.driver.md)**: The `constructs` folder in the `python-backend` codebase contains CDK constructs for various AWS services, including Lambda functions for asset onboarding and metrics processing, an AWS WAF setup, a backend service deployment, and infrastructure management for AWS Inspector.

## Files
- **[__init__.py](cdk/__init__.py.driver.md)**: Empty file (no analyzable contents).
- **[development_stack.py](cdk/development_stack.py.driver.md)**: The `development_stack.py` file defines a development environment stack using AWS CDK, incorporating components such as a metrics lambda, API backend, asset onboarding lambda, and inspector with specific parameters for development.
- **[ops_stack.py](cdk/ops_stack.py.driver.md)**: The `ops_stack.py` file defines an AWS CDK stack for the operations environment, setting up backend services, asset onboarding, inspection, and metrics collection.
- **[production_stack.py](cdk/production_stack.py.driver.md)**: The `production_stack.py` file defines a production stack using AWS CDK, incorporating components such as a metrics lambda, API backend, asset onboarding lambda, and inspector, all configured for a production environment.
- **[staging_stack.py](cdk/staging_stack.py.driver.md)**: The `staging_stack.py` file defines a CDK stack for the staging environment, incorporating components such as a metrics lambda, API backend, asset onboarding lambda, and an inspector.
- **[test_in_dev_stack.py](cdk/test_in_dev_stack.py.driver.md)**: The `test_in_dev_stack.py` file defines a CDK stack for manually deploying additional infrastructure for testing purposes in a development environment.
