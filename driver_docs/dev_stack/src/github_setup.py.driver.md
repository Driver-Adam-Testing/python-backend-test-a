# Purpose
This Python script provides a narrow functionality focused on generating a Markdown guide for setting up a GitHub App. It defines a function, `generate_markdown`, which takes a configuration dictionary as input and constructs a detailed setup guide in Markdown format, outlining steps such as creating the app, configuring webhooks, setting permissions, and testing the integration. The script also includes a function, `generate_github_app_setup_guide`, which utilizes a `GitHubAppResource` object to extract configuration data, generate the Markdown guide, and save it to a file. This code is a short script designed to automate the documentation process for GitHub App setup, making it easier for users to follow the necessary steps.
# Imports and Dependencies

---
- `models`


# Functions

---
### generate_github_app_setup_guide 
The function generates a GitHub App setup guide in markdown format and writes it to a file.
- **Inputs**:
    - `github_app_resource`: An instance of GitHubAppResource, which contains the configuration data for the GitHub App.
- **Control Flow**:
    - The function begins by dumping the configuration data from the github_app_resource object into a JSON-compatible dictionary using the model_dump method.
    - It then calls the generate_markdown function, passing the configuration dictionary to generate a markdown string that serves as the setup guide.
    - The function opens a file named 'github_app_setup_guide.md' in write mode with UTF-8 encoding in the './state/out/' directory.
    - Finally, it writes the generated markdown guide to the file and closes the file.
- **Output**:
    - The function does not return any value; it writes the generated markdown content to a file.


---
### generate_markdown 
The `generate_markdown` function creates a detailed Markdown guide for setting up a GitHub App based on a given configuration dictionary.
- **Inputs**:
    - `config`: A dictionary containing configuration details for the GitHub App, including app name, URLs, webhook settings, permissions, subscribed events, and OAuth settings.
- **Control Flow**:
    - Initialize a Markdown string with a header and instructions for creating a GitHub App, using values from the `config` dictionary.
    - Add a section for webhook configuration, populating fields with values from `config['webhook']`.
    - Iterate over `config['permissions']['repository_permissions']`, appending each permission and its level to the Markdown string.
    - Add sections for organization and account permissions, iterating over `config['permissions']['organization_permissions']` and `config['permissions']['account_permissions']` respectively, appending each permission and its level.
    - Iterate over `config['subscribed_events']`, appending each event to the Markdown string.
    - Determine the status of OAuth and device flow from `config['request_oauth_on_installation']` and `config['enable_device_flow']`, appending the status to the Markdown string.
    - Add post-setup steps and installation instructions, using values from the `config` dictionary.
    - Return the complete Markdown string.
- **Output**:
    - A string containing the complete Markdown guide for setting up a GitHub App.


