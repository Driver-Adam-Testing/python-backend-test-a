# Purpose
This Python script is designed to automate the setup, configuration, and teardown of development environments for developers, particularly in a cloud-local context. It provides a comprehensive suite of functions to create and manage various resources such as Auth0 applications, ngrok domains, GitHub apps, and database configurations. The script is structured to handle the lifecycle of these resources, from creation and configuration to eventual teardown, ensuring that developers can quickly set up their environments with minimal manual intervention. The script also generates configuration files and setup guides to assist developers in configuring their local environments, including instructions for setting up necessary tools and services like AWS CLI, Docker, and node.js.

The script is organized into several key functions, each responsible for a specific aspect of the developer environment setup. Functions like `create_developer`, `create_developer_domains`, and `create_developer_tcp_tunnel` handle the creation of developer profiles and associated resources. The `setup_developer_resources` function orchestrates the overall setup process, integrating various components such as web apps, APIs, and databases. Additionally, the script includes utility functions for loading and writing developer state to JSON files, ensuring persistence across sessions. The `generate_developer_configs` function creates detailed configuration files and a markdown setup guide, providing developers with the necessary information to configure their environments. Finally, the `teardown_developer_resources` function ensures a clean removal of all resources, maintaining a tidy development environment. This script is intended to be used as a command-line tool, providing a streamlined workflow for developers to manage their cloud-local development environments efficiently.
# Imports and Dependencies

---
- `json`
- `pathlib.Path`
- `auth0_apps.create_api_app`
- `auth0_apps.create_m2m_app`
- `auth0_apps.create_spa_web_app`
- `auth0_apps.delete_auth0_api`
- `auth0_apps.delete_auth0_app`
- `config.settings`
- `modal_scripts.build_modal_deploy_script`
- `models.ApiResourceConfig`
- `models.AssetLambdaSecretMap`
- `models.Auth0SpaCreateAppRequest`
- `models.CDKResourceConfig`
- `models.ContentServicesResource`
- `models.DatabaseResource`
- `models.DatabaseResourceConfig`
- `models.Developer`
- `models.DeveloperResource`
- `models.DeveloperResourceType`
- `models.DomainStatus`
- `models.DomainType`
- `models.GitHubAppPermissionsConfig`
- `models.GitHubAppResource`
- `models.GitHubAppWebhookConfig`
- `models.LambdaResourceConfig`
- `models.MetricsLambdaSecretMap`
- `models.ModalSecretResource`
- `models.NgrokReservedDomain`
- `models.NgrokReservedTcpAddress`
- `models.WebAppResourceConfig`
- `ngrok.create_reserved_domain`
- `ngrok.create_reserved_tcp_address`
- `ngrok.delete_reserved_domain`
- `ngrok.delete_reserved_tcp_address`
- `ngrok.generate_unique_subdomain`
- `utils.generate_webhook_secret`


# Functions

---
### create_developer 
The `create_developer` function initializes and returns a `Developer` object with specified full name, email, and an optional region.
- **Inputs**:
    - `full_name`: A string representing the full name of the developer.
    - `email`: A string representing the email address of the developer.
    - `region`: An optional string representing the region of the developer, defaulting to 'us'.
- **Control Flow**:
    - The function directly returns a new `Developer` object.
    - The `Developer` object is initialized with the provided `full_name`, `email`, and `region`.
- **Output**:
    - A `Developer` object initialized with the provided full name, email, and region.


---
### create_developer_domains 
The `create_developer_domains` function generates and reserves unique subdomains for a developer based on specified domain types using the Ngrok API.
- **Inputs**:
    - `developer`: An instance of the Developer class representing the developer for whom the domains are being created.
    - `domain_types`: A list of DomainType instances specifying the types of domains to be created for the developer.
    - `ngrok_api_key`: A string representing the API key used to authenticate with the Ngrok service.
- **Control Flow**:
    - Initialize an empty list `results` to store the reserved domain information.
    - Iterate over each `app_type` in the `domain_types` list.
    - For each `app_type`, generate a unique subdomain using the developer's full name and the domain type as a prefix.
    - Create a description for the reserved domain using the developer's full name and the domain type.
    - Call `create_reserved_domain` with the Ngrok API key, generated subdomain, description, and developer's region to reserve the domain.
    - If the domain is successfully reserved, append a new `NgrokReservedDomain` instance to the `results` list with the domain details.
    - Return the `results` list containing all successfully reserved domains.
- **Output**:
    - A list of NgrokReservedDomain instances representing the reserved domains, or None if no domains were reserved.


---
### create_developer_resource_configs 
The `create_developer_resource_configs` function generates configuration dictionaries for various developer resources based on the developer's reserved domains and resource types.
- **Inputs**:
    - `developer`: An instance of the Developer class containing information about the developer's resources, reserved domains, and other related configurations.
- **Control Flow**:
    - Initialize an empty dictionary `resource_configs` to store the configurations.
    - Identify the web application domain from the developer's reserved domains.
    - Iterate over each resource in the developer's resources list.
    - For each resource, use a match-case statement to determine the resource type and generate the appropriate configuration.
    - For `WEB_APP` resources, create a `WebAppResourceConfig` with setup instructions, Vite configuration, and environment variables.
    - For `API` resources, create an `ApiResourceConfig` with environment variables for API setup.
    - For `GITHUB_APP` resources, directly use the resource's existing configuration.
    - For `ASSET_ONBOARDING_LAMBDA` and `METRICS_LAMBDA` resources, create a `LambdaResourceConfig` with environment variables and secret maps.
    - For `DB` resources, create a `DatabaseResourceConfig` with database URLs.
    - For `CDK_STACK` resources, create a `CDKResourceConfig` with CLI execution instructions and environment variables.
    - For `CONTENT_SERVICES` resources, create a `ContentServicesResource` with modal environment and secret resources.
    - Return the `resource_configs` dictionary containing all generated configurations.
- **Output**:
    - A dictionary where each key is a resource name and each value is the JSON-dumped configuration for that resource.


---
### create_developer_tcp_tunnel 
The `create_developer_tcp_tunnel` function creates a reserved TCP address for a developer using the ngrok API.
- **Inputs**:
    - `developer`: An instance of the Developer class, representing the developer for whom the TCP tunnel is being created.
    - `ngrok_api_key`: A string representing the API key for accessing the ngrok service.
- **Control Flow**:
    - A description string is created using the developer's full name.
    - The function attempts to create a reserved TCP address by calling `create_reserved_tcp_address` with the provided API key, description, region, and metadata.
    - If the TCP address creation is successful, the function returns the created NgrokReservedTcpAddress object.
    - If an exception occurs during the creation process, an error message is printed and the function returns None.
- **Output**:
    - The function returns an NgrokReservedTcpAddress object if successful, or None if an error occurs.


---
### generate_developer_configs 
The `generate_developer_configs` function generates resource configuration files and a setup guide for a specified developer.
- **Inputs**:
    - `name`: The name of the developer for whom the configuration files are to be generated.
    - `output_dir`: The directory where the generated configuration files and setup guide will be saved.
- **Control Flow**:
    - The function begins by loading the developer's state using the `load_developer_state` function with the provided `name`.
    - If the developer's state cannot be loaded, a `ValueError` is raised indicating that no state file was found for the developer.
    - An output directory is created if it does not already exist using `Path(output_dir).mkdir(exist_ok=True)`.
    - The function calls `create_developer_resource_configs` to generate configuration data for the developer's resources.
    - A markdown setup guide is created and written to a file named `setup_guide.md` in the output directory.
    - The setup guide includes an overview, prerequisites, AWS CLI configuration, and instructions for setting up, regenerating configs, running tunnels, and tearing down the development stack.
    - For each resource configuration, the function writes the configuration to a JSON file in the output directory and documents it in the setup guide.
    - Special handling is provided for the 'content-services' resource, where modal secrets and deployment scripts are generated and written to shell scripts.
- **Output**:
    - The function does not return any value; it performs file operations to generate configuration files and a setup guide in the specified output directory.


---
### load_developer_state 
The `load_developer_state` function loads and validates a developer's state from a JSON file based on their full name.
- **Inputs**:
    - `full_name`: A string representing the full name of the developer, used to construct the filename for the state file.
- **Control Flow**:
    - Constructs a filename by converting the full name to lowercase, replacing spaces with underscores, and appending '_state.json'.
    - Creates a file path by joining the 'state' directory with the constructed filename.
    - Checks if the file path exists; if not, prints an error message and returns None.
    - Attempts to open the file and load its JSON content.
    - Validates the loaded JSON content using the `Developer.model_validate` method.
    - If any exception occurs during file reading or JSON loading, prints an error message and returns None.
- **Output**:
    - Returns a `Developer` object if the state is successfully loaded and validated, otherwise returns None.


---
### setup_developer_resources 
The `setup_developer_resources` function initializes and configures various development resources for a developer, including domains, TCP tunnels, Auth0 applications, GitHub apps, and database resources.
- **Inputs**:
    - `full_name`: The full name of the developer for whom the resources are being set up.
    - `email`: The email address of the developer.
    - `region`: The region in which the resources should be set up, defaulting to 'us'.
    - `setup_github`: A boolean flag indicating whether to set up GitHub resources, defaulting to True.
- **Control Flow**:
    - Retrieve the ngrok API key from settings.
    - Create a Developer object using the provided full name, email, and region.
    - Define domain types for WEBAPP and API and create reserved domains for the developer using ngrok.
    - Extend the developer's reserved domains with the created domains.
    - Create a TCP tunnel for the developer using ngrok and assign it to the developer's reserved TCP address if successful.
    - Identify the web app domain from the reserved domains and print its domain.
    - Create an Auth0 SPA web app using the web app domain and assign it to the developer.
    - Identify the API domain from the reserved domains and create an Auth0 API app using its URL as the identifier.
    - Create an Auth0 M2M app using the API domain's URL as the identifier.
    - Set up a GitHub app resource with specific permissions and webhook configurations if setup_github is True.
    - Create a database resource using settings and the developer's reserved TCP address.
    - Assign the created Auth0 apps, GitHub app, and database resource to the developer.
    - Create various DeveloperResource objects for web app, API, M2M, database, asset onboarding lambda, metrics lambda, content services, and CDK stack.
    - Assign the created resources to the developer's resources list.
    - Write the developer's state to a file using the write_developer_state function.
    - Return the configured Developer object.
- **Output**:
    - A Developer object with all the configured resources and state.


---
### teardown_developer_resources 
The function `teardown_developer_resources` removes various resources associated with a developer, including Auth0 applications, ngrok domains, and local files, and returns a boolean indicating success.
- **Inputs**:
    - `developer`: An instance of the Developer class containing information about the developer's resources to be deleted.
- **Control Flow**:
    - Initialize a success flag as True.
    - Attempt to delete the Auth0 web application using its client ID; set success to False if deletion fails.
    - Attempt to delete the Auth0 machine-to-machine application using its client ID; set success to False if deletion fails.
    - Attempt to delete the Auth0 API using its ID; set success to False if deletion fails.
    - Iterate over each reserved domain in the developer's reserved domains list and attempt to delete it using its metadata ID; set success to False if any deletion fails.
    - Attempt to delete the reserved TCP address using its metadata ID; set success to False if deletion fails.
    - Try to delete the developer's state file from the 'state' directory; catch exceptions and set success to False if an error occurs.
    - Try to delete the 'state/out' configuration directory using shutil.rmtree; catch exceptions and set success to False if an error occurs.
    - Try to delete the 'gh.html' file from the 'static' directory; catch exceptions and set success to False if an error occurs.
    - Return the success flag indicating whether all deletions were successful.
- **Output**:
    - A boolean value indicating whether all resources were successfully deleted (True) or if any deletion failed (False).


---
### write_developer_state 
The `write_developer_state` function writes the state of a `Developer` object to a JSON file in a specified directory.
- **Inputs**:
    - `developer`: A `Developer` object whose state is to be saved to a file.
    - `output_dir`: An optional string specifying the directory where the state file will be saved, defaulting to 'state'.
- **Control Flow**:
    - The function first ensures that the specified output directory exists by creating it if it does not.
    - It constructs a filename for the JSON file by converting the developer's full name to lowercase, replacing spaces with underscores, and appending '_state.json'.
    - The function then opens the file in write mode and uses `json.dump` to serialize the developer's state, obtained via `developer.model_dump(mode='json')`, into the file with an indentation of 2 spaces.
    - Finally, it prints a confirmation message indicating the file path where the developer's state has been written.
- **Output**:
    - The function does not return any value; it performs file writing as a side effect.


