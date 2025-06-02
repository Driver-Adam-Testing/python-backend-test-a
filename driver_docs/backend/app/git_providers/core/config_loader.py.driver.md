# Purpose
This Python code defines a function, `load_provider_config`, which is designed to load and return a configuration object for a Git provider application, specifically for GitLab Enterprise Self-Managed instances. The function takes a `GitProviderApp` object and an optional `client_secret` as parameters, and it returns a `GitProviderConfig` object populated with various attributes such as application ID, name, provider kind, and several endpoint URLs necessary for OAuth authentication. The code provides narrow functionality, focusing solely on configuring GitLab Enterprise Self-Managed applications, and raises a `ValueError` if an unsupported provider kind is encountered. This script is a utility function that likely forms part of a larger system dealing with multiple Git provider configurations.
# Imports and Dependencies

---
- `app.git_providers.core.config`
- `database.models_v1`


# Functions

---
### load_provider_config 
The function `load_provider_config` creates a `GitProviderConfig` object for a supported Git provider application, specifically for GitLab Enterprise Self-Managed, using the provided application details and an optional client secret.
- **Inputs**:
    - `app`: An instance of `GitProviderApp` containing details about the Git provider application, such as its ID, name, provider kind, base URL, client ID, redirect URI, and scopes.
    - `client_secret`: An optional string representing the client secret for the Git provider application, which defaults to `None` if not provided.
- **Control Flow**:
    - Check if the `provider_kind` of the `app` is `GitProviderKind.GITLAB_ENTERPRISE_SELF_MANAGED`.
    - If the provider kind is supported, return a `GitProviderConfig` object initialized with the application's details and endpoints specific to GitLab Enterprise Self-Managed.
    - If the provider kind is not supported, raise a `ValueError` indicating the unsupported provider.
- **Output**:
    - A `GitProviderConfig` object configured with the application's details and specific endpoints for GitLab Enterprise Self-Managed, or raises a `ValueError` if the provider is unsupported.


