# Purpose
This Python code defines a configuration management system using the Pydantic library, specifically tailored for applications that require environment-based settings. The primary component is the `Settings` class, which inherits from `BaseSettings` provided by Pydantic. This class encapsulates various configuration parameters such as API endpoints, authentication credentials, AWS settings, and GitHub integration details. The settings are designed to be loaded from environment variables, with defaults specified in the class. The `SettingsConfigDict` is used to specify that the environment variables should be read from a `.env` file, and any extra variables should be ignored. The code also includes a utility function, `parse_cors`, to handle CORS origin parsing, which is integrated into the settings via Pydantic's `BeforeValidator`.

A notable feature of this configuration system is the validation mechanism that checks for default secret values. The `model_validator` method `_check_non_default_secrets` ensures that any sensitive information, initially set to a placeholder value (`DEFAULT_SECRET`), is replaced with actual secure values before deployment. If the application is running in a local environment, a warning is issued; otherwise, a `ValueError` is raised to prevent deployment with insecure defaults. This code is intended to be used as a configuration module within a larger application, providing a structured and secure way to manage environment-specific settings.
# Imports and Dependencies

---
- `warnings`
- `typing.Annotated`
- `typing.Literal`
- `typing.Self`
- `pydantic.AnyUrl`
- `pydantic.BeforeValidator`
- `pydantic.model_validator`
- `pydantic_settings.BaseSettings`
- `pydantic_settings.SettingsConfigDict`


# Global Variables

---
### ACCESS_TOKEN_EXPIRE_MINUTES 
- **Type**: `int`
- **Description**: `ACCESS_TOKEN_EXPIRE_MINUTES` is an integer variable that defines the expiration time for access tokens in minutes. It is set to 60 minutes multiplied by 24 hours and 8 days, resulting in a total of 11,520 minutes, which equates to 8 days.
- **Use**: This variable is used to configure the duration for which an access token remains valid before it expires.


---
### API_V1_STR 
- **Type**: `str`
- **Description**: `API_V1_STR` is a string variable defined within the `Settings` class, which inherits from `BaseSettings`. It is set to the value `'/api/v1'`, indicating the base path for version 1 of the API.
- **Use**: This variable is used to define the base URL path for version 1 of the API endpoints in the application.


---
### AUTH0_AUDIENCE 
- **Type**: `str`
- **Description**: `AUTH0_AUDIENCE` is a global variable defined within the `Settings` class, which inherits from `BaseSettings`. It is initialized with the default value `DEFAULT_SECRET`, indicating that it is a placeholder for the Auth0 audience identifier used in authentication processes.
- **Use**: This variable is used to store the Auth0 audience identifier, which should be replaced with a specific value before deployment to ensure proper authentication.


---
### AUTH0_CLIENT_ID 
- **Type**: `str`
- **Description**: `AUTH0_CLIENT_ID` is a global variable defined within the `Settings` class, which inherits from `BaseSettings`. It is intended to store the client ID for Auth0 authentication, a service used for identity management. The variable is initialized with a default value of `DEFAULT_SECRET`, indicating that it should be replaced with a real client ID before deployment.
- **Use**: This variable is used to configure the Auth0 client ID for authentication purposes in the application.


---
### AUTH0_DOMAIN 
- **Type**: `str`
- **Description**: `AUTH0_DOMAIN` is a global variable defined within the `Settings` class, which inherits from `BaseSettings`. It is intended to store the domain for Auth0 authentication services. By default, it is set to the value of `DEFAULT_SECRET`, which is a placeholder string 'changethis' indicating that it should be replaced with a real value before deployment.
- **Use**: This variable is used to configure the domain for Auth0 authentication, and it is expected to be set to a valid domain string in a production environment.


---
### AUTH0_MGMT_API_AUDIENCE 
- **Type**: `str`
- **Description**: `AUTH0_MGMT_API_AUDIENCE` is a global variable defined within the `Settings` class, which inherits from `BaseSettings`. It is initialized with the default value `DEFAULT_SECRET`, indicating that it is a placeholder for the Auth0 Management API audience identifier.
- **Use**: This variable is used to store the audience identifier for the Auth0 Management API, which is essential for configuring authentication and authorization settings.


---
### AUTH0_MGMT_API_CLIENT_ID 
- **Type**: `str`
- **Description**: `AUTH0_MGMT_API_CLIENT_ID` is a global variable defined within the `Settings` class, which inherits from `BaseSettings`. It is initialized with a default value of `DEFAULT_SECRET`, indicating that it is intended to be replaced with a specific client ID for the Auth0 Management API in a production environment.
- **Use**: This variable is used to store the client ID for the Auth0 Management API, which is essential for authenticating API requests.


---
### AUTH0_MGMT_API_CLIENT_SECRET 
- **Type**: `str`
- **Description**: `AUTH0_MGMT_API_CLIENT_SECRET` is a global variable defined within the `Settings` class, which inherits from `BaseSettings`. It is intended to store the client secret for the Auth0 Management API, a critical piece of information used for authenticating API requests.
- **Use**: This variable is used to configure the client secret for the Auth0 Management API, and it defaults to a placeholder value `DEFAULT_SECRET` which should be changed in production environments.


---
### AUTH0_MGMT_API_DOMAIN 
- **Type**: `str`
- **Description**: `AUTH0_MGMT_API_DOMAIN` is a global variable defined within the `Settings` class, which inherits from `BaseSettings`. It is initialized with a default value of `DEFAULT_SECRET`, indicating that it is intended to be replaced with a specific domain value for the Auth0 Management API in a production environment.
- **Use**: This variable is used to store the domain for the Auth0 Management API, which is essential for configuring authentication and authorization services.


---
### AWS_ACCESS_KEY_ID 
- **Type**: `str`
- **Description**: `AWS_ACCESS_KEY_ID` is a global variable defined within the `Settings` class, which inherits from `BaseSettings`. It is intended to store the AWS access key ID, a credential used to authenticate requests to AWS services. The variable is initialized with a default value of `DEFAULT_SECRET`, indicating that it should be replaced with a valid access key ID before deployment.
- **Use**: This variable is used to store and manage the AWS access key ID for authenticating AWS service requests within the application.


---
### AWS_REGION 
- **Type**: `str`
- **Description**: `AWS_REGION` is a global variable defined within the `Settings` class, which inherits from `BaseSettings`. It is intended to store the AWS region identifier, which is crucial for configuring AWS services to operate in a specific geographical area. The default value for this variable is set to `DEFAULT_SECRET`, indicating that it should be replaced with an actual AWS region identifier before deployment.
- **Use**: This variable is used to specify the AWS region for the application, ensuring that AWS services are accessed in the correct geographical location.


---
### AWS_S3_CODE_BUCKET_SUFFIX 
- **Type**: `str`
- **Description**: `AWS_S3_CODE_BUCKET_SUFFIX` is a global variable defined within the `Settings` class, which inherits from `BaseSettings`. It is initialized with a default value of `DEFAULT_SECRET`, indicating that it is a placeholder value that should be changed before deployment. This variable is likely intended to store a suffix for an AWS S3 bucket name, which is used in the application's configuration.
- **Use**: This variable is used to configure the suffix for an AWS S3 bucket name, and it should be set to a specific value before deploying the application.


---
### AWS_S3_ENDPOINT_URL 
- **Type**: `str | None`
- **Description**: `AWS_S3_ENDPOINT_URL` is a global variable defined within the `Settings` class, which inherits from `BaseSettings`. It is intended to store the endpoint URL for an AWS S3 service, allowing the application to connect to a specific S3 instance. The variable is initialized with a default value of `None`, indicating that it may not be required in all environments or configurations.
- **Use**: This variable is used to configure the endpoint URL for AWS S3, which can be set through environment variables or configuration files.


---
### AWS_SECRET_ACCESS_KEY 
- **Type**: `str`
- **Description**: `AWS_SECRET_ACCESS_KEY` is a global variable defined within the `Settings` class, which inherits from `BaseSettings`. It is intended to store the secret access key for AWS services, and is initialized with a default placeholder value `DEFAULT_SECRET`. This variable is part of the configuration settings that can be loaded from an environment file or other sources.
- **Use**: This variable is used to securely store and manage the AWS secret access key needed for authenticating requests to AWS services.


---
### BACKEND_CORS_ORIGINS 
- **Type**: `Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)]`
- **Description**: The `BACKEND_CORS_ORIGINS` variable is a global configuration setting within the `Settings` class, which is part of a Pydantic-based configuration management system. It is annotated to be either a list of URLs or a string, and it uses a custom validator `parse_cors` to ensure the input is correctly formatted. This variable is intended to specify the allowed origins for Cross-Origin Resource Sharing (CORS) in the backend application.
- **Use**: This variable is used to configure which origins are permitted to access the backend resources, ensuring proper CORS policy enforcement.


---
### DEFAULT_SECRET 
- **Type**: `str`
- **Description**: `DEFAULT_SECRET` is a global string variable initialized with the value 'changethis'. It serves as a placeholder for sensitive information such as API keys, client secrets, and other credentials in the `Settings` class.
- **Use**: This variable is used as a default value for various sensitive configuration fields in the `Settings` class, prompting users to replace it with actual secrets before deployment.


---
### DOMAIN 
- **Type**: `str`
- **Description**: The `DOMAIN` variable is a global configuration setting within the `Settings` class, which is a subclass of `BaseSettings` from the `pydantic_settings` module. It is initialized with the default value of 'localhost', indicating that the application is likely intended to run on a local server by default.
- **Use**: This variable is used to specify the domain name for the application, which can be configured through environment variables or an `.env` file.


---
### DROPZONE_BUCKET_NAME 
- **Type**: `str`
- **Description**: `DROPZONE_BUCKET_NAME` is a global variable defined within the `Settings` class, which inherits from `BaseSettings`. It is initialized with a default value of `DEFAULT_SECRET`, indicating that it is intended to be replaced with a specific value for the name of an S3 bucket used for a dropzone in an AWS environment.
- **Use**: This variable is used to store the name of the S3 bucket designated for dropzone operations, and it should be configured with a valid bucket name before deployment.


---
### ENVIRONMENT 
- **Type**: `Literal['local', 'development', 'staging', 'production']`
- **Description**: The `ENVIRONMENT` variable is a global configuration setting within the `Settings` class, defined as a literal type that can take one of four string values: 'local', 'development', 'staging', or 'production'. This variable is used to specify the current operational environment of the application, which can affect how the application behaves, particularly in terms of configuration and deployment.
- **Use**: This variable is used to determine the operational environment of the application, influencing configuration and deployment settings.


---
### GH_CLIENT_ID 
- **Type**: `str`
- **Description**: `GH_CLIENT_ID` is a global variable defined within the `Settings` class, which inherits from `BaseSettings`. It is initialized with the default value `DEFAULT_SECRET`, indicating that it is intended to be replaced with a specific GitHub client ID for authentication purposes.
- **Use**: This variable is used to store the GitHub client ID, which is essential for authenticating API requests to GitHub services.


---
### GH_CLIENT_PEM_SECRET 
- **Type**: `str`
- **Description**: `GH_CLIENT_PEM_SECRET` is a global variable defined within the `Settings` class, which inherits from `BaseSettings`. It is initialized with a default value of `DEFAULT_SECRET`, which is a placeholder string 'changethis'. This variable is intended to store the GitHub Client PEM (Privacy Enhanced Mail) secret, which is a sensitive credential used for authentication purposes.
- **Use**: This variable is used to store and manage the GitHub Client PEM secret, ensuring it is set to a secure value before deployment.


---
### GH_CLIENT_SECRET 
- **Type**: `str`
- **Description**: `GH_CLIENT_SECRET` is a global variable defined within the `Settings` class, which inherits from `BaseSettings`. It is intended to store the GitHub client secret, a sensitive credential used for authenticating API requests to GitHub services. The default value for this variable is set to `DEFAULT_SECRET`, which is a placeholder string 'changethis' that should be replaced with an actual secret in a production environment.
- **Use**: This variable is used to configure the GitHub client secret for authentication purposes in the application.


---
### GH_REDIRECT_URI 
- **Type**: `str`
- **Description**: `GH_REDIRECT_URI` is a global variable defined within the `Settings` class, which inherits from `BaseSettings`. It is initialized with a default value of `DEFAULT_SECRET`, indicating that it is a placeholder for a GitHub OAuth redirect URI.
- **Use**: This variable is used to store the redirect URI for GitHub OAuth authentication, and it should be set to a specific URI before deployment to ensure proper functionality.


---
### GH_WEBHOOK_SECRET 
- **Type**: `str`
- **Description**: `GH_WEBHOOK_SECRET` is a global variable defined within the `Settings` class, which inherits from `BaseSettings`. It is initialized with the value of `DEFAULT_SECRET`, which is a placeholder string 'changethis'. This variable is intended to store the secret key used for verifying GitHub webhook payloads.
- **Use**: This variable is used to store and manage the secret key for GitHub webhook verification, ensuring secure communication between the application and GitHub.


---
### HOST 
- **Type**: `str`
- **Description**: The `HOST` variable is a global configuration setting within the `Settings` class, defined as a string with the default value of "127.0.0.1". This variable is used to specify the host address for the application, typically representing the local machine in a development environment.
- **Use**: The `HOST` variable is used to configure the host address for the application, allowing it to bind to the specified IP address.


---
### INSPECTOR_BUCKET_NAME 
- **Type**: `str`
- **Description**: `INSPECTOR_BUCKET_NAME` is a global variable defined within the `Settings` class, which inherits from `BaseSettings`. It is initialized with the default value of `DEFAULT_SECRET`, indicating that it is a placeholder value meant to be replaced with a specific string representing the name of an S3 bucket used for inspection purposes.
- **Use**: This variable is used to store the name of an S3 bucket, which is likely utilized for inspection-related operations within the application.


---
### LOG_LEVEL 
- **Type**: `str`
- **Description**: The `LOG_LEVEL` variable is a global configuration setting within the `Settings` class, defined as a string with a default value of "INFO". It is used to specify the logging level for the application, which determines the severity of messages that will be logged.
- **Use**: This variable is used to control the verbosity of log output in the application.


---
### MODAL_ENVIRONMENT 
- **Type**: `str`
- **Description**: `MODAL_ENVIRONMENT` is a global variable defined within the `Settings` class, which inherits from `BaseSettings`. It is initialized with the default value of `DEFAULT_SECRET`, which is a placeholder string 'changethis'. This variable is intended to store the environment configuration for a modal, which could be used to differentiate between various deployment environments.
- **Use**: This variable is used to configure the environment settings for a modal, and it should be updated from its default value before deployment.


---
### PORT 
- **Type**: `int`
- **Description**: The `PORT` variable is an integer that specifies the port number on which the application will run. It is set to 8000 by default, indicating the default port for the server to listen for incoming connections.
- **Use**: This variable is used to configure the network port for the application's server.


---
### PROJECT_NAME 
- **Type**: `str`
- **Description**: `PROJECT_NAME` is a global variable defined within the `Settings` class, which inherits from `BaseSettings`. It is intended to store the name of the project as a string. By default, it is set to `DEFAULT_SECRET`, indicating that it should be customized before deployment.
- **Use**: This variable is used to hold the name of the project, which can be configured through environment variables or directly in the code.


---
### SENTRY_DSN 
- **Type**: `str | None`
- **Description**: `SENTRY_DSN` is a global variable defined within the `Settings` class, which is a subclass of `BaseSettings` from the `pydantic_settings` module. It is intended to store the Data Source Name (DSN) for Sentry, a service used for error tracking and monitoring in applications. The variable is of type `str` or `None`, indicating that it can either hold a string value representing the DSN or be set to `None` if not configured.
- **Use**: This variable is used to configure the Sentry DSN for error tracking in the application.


---
### USE_LEGACY_DROPZONE 
- **Type**: `bool | None`
- **Description**: `USE_LEGACY_DROPZONE` is a global variable defined within the `Settings` class, which is a subclass of `BaseSettings` from the `pydantic_settings` module. It is a boolean or None type variable that defaults to `True`. This variable likely indicates whether to use a legacy version of a dropzone feature or service.
- **Use**: This variable is used to configure the application settings, specifically to determine if the legacy dropzone functionality should be enabled.


---
### model_config 
- **Type**: `SettingsConfigDict`
- **Description**: The `model_config` variable is an instance of `SettingsConfigDict` used within the `Settings` class, which inherits from `BaseSettings`. It is configured to read environment variables from a file named `.env`, ignore empty environment variables, and ignore any extra fields not defined in the settings model. This configuration helps manage application settings by loading them from environment variables, which is a common practice for managing configuration in different environments.
- **Use**: This variable is used to configure how environment variables are loaded and managed within the `Settings` class.


---
### settings 
- **Type**: `Settings`
- **Description**: The `settings` variable is an instance of the `Settings` class, which is a subclass of `BaseSettings` from the `pydantic_settings` module. This class is designed to manage application configuration, loading settings from environment variables or a `.env` file. It includes various configuration options such as API paths, token expiration times, domain settings, authentication credentials, AWS configuration, GitHub integration, and logging levels.
- **Use**: The `settings` variable is used to access and manage application configuration settings throughout the application, ensuring that all necessary environment-specific configurations are loaded and validated.


# Classes

---
### Settings 
- **Type**: `class`
- **Members**:
    - `model_config`: Configuration for environment file and extra settings.
    - `API_V1_STR`: String representing the API version 1 endpoint.
    - `ACCESS_TOKEN_EXPIRE_MINUTES`: Duration in minutes for which the access token is valid.
    - `DOMAIN`: Domain name for the application.
    - `ENVIRONMENT`: Current environment setting, e.g., local, development, etc.
    - `AUTH0_DOMAIN`: Domain for Auth0 authentication, defaulting to a placeholder secret.
    - `AUTH0_CLIENT_ID`: Client ID for Auth0, defaulting to a placeholder secret.
    - `AUTH0_AUDIENCE`: Audience for Auth0, defaulting to a placeholder secret.
    - `AUTH0_MGMT_API_DOMAIN`: Domain for Auth0 Management API, defaulting to a placeholder secret.
    - `AUTH0_MGMT_API_CLIENT_ID`: Client ID for Auth0 Management API, defaulting to a placeholder secret.
    - `AUTH0_MGMT_API_CLIENT_SECRET`: Client secret for Auth0 Management API, defaulting to a placeholder secret.
    - `AUTH0_MGMT_API_AUDIENCE`: Audience for Auth0 Management API, defaulting to a placeholder secret.
    - `AWS_ACCESS_KEY_ID`: Access key ID for AWS, defaulting to a placeholder secret.
    - `AWS_SECRET_ACCESS_KEY`: Secret access key for AWS, defaulting to a placeholder secret.
    - `AWS_REGION`: AWS region, defaulting to a placeholder secret.
    - `AWS_S3_ENDPOINT_URL`: Endpoint URL for AWS S3, which can be None.
    - `AWS_S3_CODE_BUCKET_SUFFIX`: Suffix for AWS S3 code bucket, defaulting to a placeholder secret.
    - `DROPZONE_BUCKET_NAME`: Name of the dropzone bucket, defaulting to a placeholder secret.
    - `USE_LEGACY_DROPZONE`: Boolean indicating whether to use legacy dropzone, defaulting to True.
    - `INSPECTOR_BUCKET_NAME`: Name of the inspector bucket, defaulting to a placeholder secret.
    - `PORT`: Port number for the application, defaulting to 8000.
    - `HOST`: Host address for the application, defaulting to 127.0.0.1.
    - `GH_CLIENT_ID`: GitHub client ID, defaulting to a placeholder secret.
    - `GH_CLIENT_SECRET`: GitHub client secret, defaulting to a placeholder secret.
    - `GH_REDIRECT_URI`: Redirect URI for GitHub, defaulting to a placeholder secret.
    - `GH_WEBHOOK_SECRET`: Webhook secret for GitHub, defaulting to a placeholder secret.
    - `GH_CLIENT_PEM_SECRET`: PEM secret for GitHub client, defaulting to a placeholder secret.
    - `MODAL_ENVIRONMENT`: Environment setting for modal, defaulting to a placeholder secret.
    - `SENTRY_DSN`: Data Source Name for Sentry, which can be None.
    - `LOG_LEVEL`: Logging level for the application, defaulting to INFO.
    - `BACKEND_CORS_ORIGINS`: List or string of allowed CORS origins, validated by a custom parser.
    - `PROJECT_NAME`: Name of the project, defaulting to a placeholder secret.
- **Description**: The `Settings` class is a configuration class that extends `BaseSettings` from Pydantic, designed to manage application settings and environment variables. It includes a variety of configuration options such as API endpoints, authentication credentials, AWS settings, and more, with many fields defaulting to a placeholder secret that must be changed before deployment. The class also includes a model validator to ensure that default secrets are not used in non-local environments, raising warnings or errors as appropriate. This class is essential for managing and validating configuration settings in a structured and secure manner.
- **Inherits From**:
    - BaseSettings

**Methods**

---
#### Settings._check_non_default_secrets
The `_check_non_default_secrets` function checks for fields in the settings model that have not been changed from their default secret value and handles them accordingly.
- **Inputs**:
    - None
- **Control Flow**:
    - Iterates over each field in the `model_fields` of the settings instance.
    - For each field, retrieves the default value and the actual value from the instance.
    - Checks if the default value is a string equal to `DEFAULT_SECRET` and if the actual value is also `DEFAULT_SECRET`.
    - If both conditions are met, calls the `_handle_default_secret` method with the field name.
    - Returns the instance of the settings class (`self`).
- **Output**:
    - Returns the instance of the settings class (`self`).


---
#### Settings._handle_default_secret
The function `_handle_default_secret` checks if a configuration variable is set to a default secret value and issues a warning or raises an error based on the environment.
- **Inputs**:
    - `var_name`: A string representing the name of the configuration variable being checked.
- **Control Flow**:
    - Constructs a message indicating that the variable is set to the default secret value and needs to be changed.
    - Checks if the environment is set to 'local'.
    - If the environment is 'local', it issues a warning with the constructed message.
    - If the environment is not 'local', it raises a `ValueError` with the constructed message.
- **Output**:
    - The function does not return any value; it either issues a warning or raises an error based on the environment.



# Functions

---
### parse_cors 
The `parse_cors` function processes a given input to return a list of strings if the input is a comma-separated string, or returns the input as is if it's already a list or string, raising a ValueError otherwise.
- **Inputs**:
    - `v`: The input value which can be of any type, expected to be either a string or a list of strings.
- **Control Flow**:
    - Check if the input `v` is a string and does not start with '[', indicating it's a comma-separated list of values.
    - If the above condition is true, split the string by commas, strip whitespace from each element, and return the resulting list of strings.
    - If the input `v` is already a list or a string, return it as is.
    - If none of the above conditions are met, raise a ValueError with the input `v`.
- **Output**:
    - The function returns a list of strings if the input is a comma-separated string, or the input itself if it is already a list or string.


