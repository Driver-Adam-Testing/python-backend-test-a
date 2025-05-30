# Purpose
This Python code defines a set of data models and enumerations using the Pydantic library, which is commonly used for data validation and settings management. The primary purpose of this file is to provide structured representations of various resources and configurations related to application development and deployment, particularly in the context of Auth0, Ngrok, and GitHub integrations. The code includes models for creating Auth0 applications and APIs, managing Ngrok reserved domains and TCP addresses, and configuring various developer resources such as web applications, APIs, databases, and GitHub applications. Each model is designed to enforce data integrity and provide computed properties for generating URLs and other derived information.

The file is organized into several classes, each representing a specific type of resource or configuration. Enumerations are used to define fixed sets of values for certain fields, such as domain types and statuses. The models include fields with default values and constraints, ensuring that the data adheres to expected formats and requirements. Additionally, the code defines computed fields using Pydantic's `@computed_field` decorator, which allows for dynamic property generation based on other fields' values. This file is likely intended to be part of a larger system where these models are used to facilitate the creation, management, and deployment of various application components, providing a clear and consistent interface for developers to interact with these resources.
# Imports and Dependencies

---
- `enum`
- `re`
- `typing.Literal`
- `pydantic.BaseModel`
- `pydantic.computed_field`
- `pydantic.constr`


# Global Variables

---
### API 
- **Type**: `string`
- **Description**: `API` is a string constant that represents a specific type of developer resource in the context of the application. It is part of the `DomainType` enumeration, which categorizes different types of domains that can be reserved.
- **Use**: The `API` variable is used to define the type of a domain as an API within the application.


---
### ASSET_ONBOARDING_LAMBDA 
- **Type**: `string`
- **Description**: `ASSET_ONBOARDING_LAMBDA` is a member of the `DeveloperResourceType` enumeration, representing a specific type of resource used in the context of developer tools and services. It is likely associated with a Lambda function that facilitates the onboarding of assets within a cloud infrastructure.
- **Use**: This variable is used to categorize resources of type 'ASSET_ONBOARDING_LAMBDA' in the application.


---
### AssetLambdaSecretMap 
- **Type**: `dict`
- **Description**: `AssetLambdaSecretMap` is a global variable that stores a mapping of secret names to their corresponding output identifiers for an asset management Lambda function. It is defined as a dictionary with string keys representing the names of the secrets and string values representing the outputs associated with those secrets.
- **Use**: This variable is used to retrieve the necessary secret values for the asset management Lambda function during its execution.


---
### CDK_STACK 
- **Type**: `string`
- **Description**: `CDK_STACK` is a member of the `DeveloperResourceType` enumeration, representing a specific type of resource in a developer's environment. It is used to categorize resources related to AWS Cloud Development Kit (CDK) stacks, which are used for defining cloud infrastructure as code.
- **Use**: This variable is utilized to specify the resource type when creating or managing developer resources.


---
### CONTENT_SERVICES 
- **Type**: `str`
- **Description**: `CONTENT_SERVICES` is a member of the `DeveloperResourceType` enumeration, representing a specific type of developer resource. It is used to categorize resources related to content services within the application.
- **Use**: This variable is utilized to define and identify resources of type content services in the context of developer resource management.


---
### CREATED 
- **Type**: `dict`
- **Description**: `CREATED` is a constant defined within the `DomainStatus` enumeration class, representing the status of a domain that has been successfully created. It is used to categorize and identify the state of a domain in the system.
- **Use**: This variable is used to indicate the creation status of a domain in various domain-related operations.


---
### DB 
- **Type**: `string`
- **Description**: `DB` is a member of the `DeveloperResourceType` enumeration, representing a type of developer resource specifically designated for database resources. It is used to categorize resources within the broader context of developer tools and services.
- **Use**: `DB` is utilized to identify and differentiate database resources in the application.


---
### DOCKER 
- **Type**: `Literal`
- **Description**: `DOCKER` is a member of the `DeveloperResourceType` enumeration, representing a specific type of developer resource related to Docker. It is used to categorize resources that are associated with Docker technology within the application.
- **Use**: This variable is used to identify and manage resources of type Docker in the context of developer resource configurations.


---
### FAILED 
- **Type**: `string`
- **Description**: `FAILED` is a member of the `DomainStatus` enumeration, representing a state where a domain creation or operation has failed. It is used to categorize and manage the status of domain-related operations within the application.
- **Use**: This variable is used to indicate the failure status of a domain in the context of domain management.


---
### GITHUB_APP 
- **Type**: `str`
- **Description**: `GITHUB_APP` is a string constant defined within the `DeveloperResourceType` enumeration class. It represents a specific type of developer resource that is associated with GitHub applications.
- **Use**: This variable is used to categorize resources of type GitHub application within the broader context of developer resources.


---
### M2M 
- **Type**: `str`
- **Description**: `M2M` is a string variable that represents a specific type of developer resource in the context of the application, specifically indicating a Machine-to-Machine (M2M) resource type. It is part of an enumeration that categorizes various resource types, allowing for structured handling of different resource categories.
- **Use**: `M2M` is used to identify and categorize resources of type Machine-to-Machine within the application.


---
### METRICS_LAMBDA 
- **Type**: `string`
- **Description**: `METRICS_LAMBDA` is a member of the `DeveloperResourceType` enumeration, representing a specific type of resource related to metrics processing in a serverless architecture. It is used to categorize resources that are associated with metrics functionality within the application.
- **Use**: This variable is utilized to define and identify resources of type metrics in the context of developer resource management.


---
### MetricsLambdaSecretMap 
- **Type**: `dict[str, str]`
- **Description**: `MetricsLambdaSecretMap` is a dictionary that maps secret names to their corresponding output identifiers for a metrics-related Lambda function. It is specifically designed to store sensitive information such as database URLs in a secure manner.
- **Use**: This variable is used to retrieve the secret output identifiers needed for configuring the metrics Lambda function.


---
### PermissionAccess 
- **Type**: `Literal`
- **Description**: `PermissionAccess` is a type alias defined as a `Literal` that can take one of three string values: 'read-only', 'read-write', or 'no-access'. This variable is used to specify the level of access permissions for resources in a structured manner.
- **Use**: It is utilized in the `GitHubAppPermissionsConfig` class to define the permissions associated with repositories, organizations, and accounts.


---
### S3_BUCKET 
- **Type**: `string`
- **Description**: `S3_BUCKET` is a string constant that represents a specific type of developer resource in the application, specifically indicating an Amazon S3 bucket. It is part of the `DeveloperResourceType` enumeration, which categorizes various resource types used in the application.
- **Use**: `S3_BUCKET` is used to identify and manage resources of type S3 bucket within the developer resource management system.


---
### TCP 
- **Type**: `enum`
- **Description**: `TCP` is a member of the `DomainType` enumeration, representing a specific type of domain used in the context of networking or application deployment. It is one of several predefined constants that categorize the nature of a domain, with `TCP` indicating that the domain is intended for TCP (Transmission Control Protocol) connections.
- **Use**: `TCP` is used to specify the domain type when creating or managing network resources.


---
### WEBAPP 
- **Type**: `string`
- **Description**: `WEBAPP` is a member of the `DomainType` enumeration, representing a specific type of domain used in the application. It is defined as a constant with the value 'WEB_APP', indicating that it is intended for web application domains.
- **Use**: This variable is used to categorize and identify domain types within the application.


---
### WEB_APP 
- **Type**: `string`
- **Description**: `WEB_APP` is a constant defined within the `DomainType` enumeration, representing a type of domain specifically for web applications. It is used to categorize resources and configurations related to web applications in the system.
- **Use**: This variable is used to identify and differentiate web application resources in various data structures and requests.


---
### allow_offline_access 
- **Type**: `boolean`
- **Description**: The `allow_offline_access` variable is a boolean flag that indicates whether offline access is permitted for the Auth0 API application. When set to `True`, it allows the application to obtain refresh tokens that can be used to access resources without requiring user interaction.
- **Use**: This variable is used to configure the Auth0 API application settings.


---
### allow_skip_consent 
- **Type**: `boolean`
- **Description**: The `allow_skip_consent` variable is a boolean flag that indicates whether users can bypass consent for verifiable first-party clients in the context of an Auth0 API request. This variable is part of the `Auth0ApiCreateRequest` class, which models the data structure for creating an Auth0 API application.
- **Use**: It is used to control the consent flow for API clients during authentication.


---
### allowed_origins 
- **Type**: `list[str] | None`
- **Description**: The `allowed_origins` variable is an optional list that can contain strings representing the origins that are permitted to access the application. If not specified, it defaults to an empty list, indicating that no origins are allowed.
- **Use**: This variable is used to define which web origins are allowed to interact with the application, typically for security and CORS (Cross-Origin Resource Sharing) purposes.


---
### app_id 
- **Type**: `string`
- **Description**: `app_id` is an optional string variable that represents the unique identifier for a GitHub application. It is part of the `GitHubAppResource` class, which encapsulates various attributes related to a GitHub app, including its name, client ID, and permissions.
- **Use**: This variable is used to store the application ID of a GitHub app, which is essential for API interactions and authentication.


---
### app_type 
- **Type**: `string`
- **Description**: The `app_type` variable is a string attribute defined in the `Auth0SpaCreateAppRequest` and `Auth0M2MCreateRequest` classes, representing the type of application being created. In `Auth0SpaCreateAppRequest`, it defaults to 'spa', while in `Auth0M2MCreateRequest`, it defaults to 'non_interactive'. This variable helps to categorize the application type for further processing.
- **Use**: It is used to specify the type of application in the context of creating requests for Auth0 applications.


---
### auth0_api 
- **Type**: `dict`
- **Description**: The `auth0_api` variable is a global variable defined within the `Developer` class, which is intended to hold configuration details related to the Auth0 API. It is structured as a dictionary, allowing for flexible storage of various settings or parameters necessary for API interactions.
- **Use**: This variable is used to store and manage the configuration settings for the Auth0 API within the context of a developer's resources.


---
### auth0_m2m 
- **Type**: `dict`
- **Description**: `auth0_m2m` is a global variable defined within the `Developer` class, representing the configuration details for an Auth0 Machine-to-Machine (M2M) application. It is expected to hold a dictionary that contains various settings and parameters necessary for the M2M application, such as its name, type, and other relevant configurations.
- **Use**: This variable is used to store and manage the configuration settings for the Auth0 M2M application associated with a developer.


---
### auth0_webapp 
- **Type**: `dict | None`
- **Description**: The `auth0_webapp` variable is a global variable defined within the `Developer` class, which is intended to hold configuration details related to an Auth0 web application. It can store various settings and parameters necessary for the web application, and it is optional, as indicated by its type allowing for `None`.
- **Use**: This variable is used to manage and access the configuration settings for the Auth0 web application associated with a developer.


---
### base64_private_key_pem 
- **Type**: `string`
- **Description**: `base64_private_key_pem` is a string variable that holds the base64-encoded representation of a private key in PEM format, which is commonly used for secure communications and authentication in various applications. This variable is part of the `GitHubAppResource` class, which encapsulates the configuration and credentials for a GitHub application.
- **Use**: This variable is used to store the private key securely in a base64 format, allowing it to be easily transmitted or stored while maintaining its integrity.


---
### client_id 
- **Type**: `string`
- **Description**: `client_id` is an optional string variable that represents the client identifier for a GitHub application. It is used to authenticate the application when making API requests.
- **Use**: This variable is utilized within the `GitHubAppResource` class to store the client ID associated with a GitHub app.


---
### client_secret 
- **Type**: `str`
- **Description**: `client_secret` is a string variable that holds the client secret for a GitHub application. This secret is used for authenticating the application with GitHub's API, ensuring secure communication.
- **Use**: It is utilized within the `GitHubAppResource` class to manage authentication and secure API requests.


---
### database 
- **Type**: `str`
- **Description**: The `database` variable is an instance of the `DatabaseResource` class, which encapsulates the configuration details necessary for connecting to a database. It includes attributes such as `db_name`, `host_address`, `user_name`, and `password`, along with computed properties for generating database connection URLs.
- **Use**: This variable is used to store and manage the database connection details for a developer's resources.


---
### enable_device_flow 
- **Type**: `boolean`
- **Description**: `enable_device_flow` is a boolean variable that indicates whether the device flow is enabled for a GitHub App resource. This feature allows users to authenticate devices that do not have a web browser, enhancing the app's usability in various environments.
- **Use**: This variable is used to control the activation of the device flow feature in the `GitHubAppResource` class.


---
### enable_permissions_in_token 
- **Type**: `boolean`
- **Description**: The `enable_permissions_in_token` variable is a boolean flag that indicates whether permissions should be included in the generated token for the Auth0 API. This variable is part of the `Auth0ApiCreateRequest` class, which is used to configure the creation of an Auth0 API application.
- **Use**: It is used to control the inclusion of permissions in the token during the API creation process.


---
### enforce_policies 
- **Type**: `boolean`
- **Description**: The `enforce_policies` variable is a boolean flag within the `Auth0ApiCreateRequest` class that indicates whether role-based access control (RBAC) policies should be enforced for the API. When set to `True`, it enables the enforcement of defined access policies, ensuring that only authorized users can access certain resources.
- **Use**: This variable is used to configure the RBAC behavior of the API during its creation.


---
### github_app 
- **Type**: `str`
- **Description**: The `github_app` variable is an instance of the `GitHubAppResource` class, which encapsulates configuration details for a GitHub application. This includes properties such as the app's name, IDs, URLs, permissions, and webhook configurations, allowing for comprehensive management of GitHub app settings.
- **Use**: It is used to store and manage the configuration of a GitHub application associated with a developer.


---
### grant_types 
- **Type**: `list[str]`
- **Description**: The `grant_types` variable is a list of strings that specifies the types of authorization grants that an application can use when interacting with an authentication server. In the context of the `Auth0SpaCreateAppRequest` and `Auth0M2MCreateRequest` classes, it defines the methods of obtaining access tokens, such as 'authorization_code', 'refresh_token', and 'client_credentials'. This variable allows for flexibility in the authentication process by enabling different grant types based on the application's requirements.
- **Use**: This variable is used to define the authorization grant types available for the application during the authentication process.


---
### include_email_in_tokens 
- **Type**: `boolean`
- **Description**: The `include_email_in_tokens` variable is a boolean flag that determines whether the user's email address should be included in the generated tokens for the Auth0 API. By default, it is set to `False`, meaning the email will not be included unless explicitly specified.
- **Use**: This variable is used in the `Auth0ApiCreateRequest` class to control the inclusion of email information in authentication tokens.


---
### initiate_login_uri 
- **Type**: `string`
- **Description**: `initiate_login_uri` is an optional string variable that holds the URI to initiate the login process for an application. It is defined within the `Auth0SpaCreateAppRequest` class, which models the request for creating a single-page application in Auth0.
- **Use**: This variable is used to specify the login URI that the application should redirect to when initiating the login process.


---
### logo_uri 
- **Type**: `string`
- **Description**: `logo_uri` is a string variable defined within the `Auth0M2MCreateRequest` class, which represents the URI of a logo associated with a machine-to-machine (M2M) application. It is an optional field that can be set to `None` if no logo is provided.
- **Use**: This variable is used to store the logo URI for M2M applications when creating an Auth0 application request.


---
### metadata 
- **Type**: `dict | None`
- **Description**: The `metadata` variable is an optional dictionary that can hold additional information related to the `NgrokReservedDomain` and `NgrokReservedTcpAddress` instances. It allows for flexible storage of extra attributes that may not be explicitly defined in the model.
- **Use**: This variable is used to store supplementary data that enhances the context of the domain or TCP address.


---
### oidc_conformant 
- **Type**: `boolean`
- **Description**: The `oidc_conformant` variable is a boolean attribute within the `Auth0SpaCreateAppRequest` class that indicates whether the application is compliant with OpenID Connect (OIDC) standards. By default, it is set to `True`, suggesting that the application is expected to follow OIDC protocols.
- **Use**: This variable is used to specify the OIDC compliance status of the application being created.


---
### organization_require_behavior 
- **Type**: `string`
- **Description**: The `organization_require_behavior` variable is a string attribute within the `Auth0SpaCreateAppRequest` class that specifies the behavior required for organization-related actions during the authentication process. It is set to 'pre_login_prompt' by default, indicating that a prompt should be displayed before the login process when organization usage is involved.
- **Use**: This variable is used to determine the behavior of the application regarding organization requirements during user authentication.


---
### organization_usage 
- **Type**: `string`
- **Description**: `organization_usage` is a string variable defined within the `Auth0SpaCreateAppRequest` class, which specifies the usage policy for organizations in the context of an Auth0 application. It is initialized with the value 'require', indicating that organization usage is mandatory for the application.
- **Use**: This variable is used to enforce organization-related policies when creating an Auth0 single-page application.


---
### private_key_pem_path 
- **Type**: `string`
- **Description**: `private_key_pem_path` is an optional string variable that holds the file path to a private key in PEM format used by a GitHub application. This path is crucial for secure authentication and communication with GitHub services.
- **Use**: This variable is used to specify the location of the private key file necessary for the GitHub application's operations.


---
### public_in_marketplace 
- **Type**: `bool`
- **Description**: `public_in_marketplace` is a boolean variable that indicates whether the GitHub application is publicly available in the marketplace. It is part of the `GitHubAppResource` class, which encapsulates various attributes related to a GitHub application.
- **Use**: This variable is used to determine the visibility of the GitHub application in the marketplace.


---
### redirect_on_update 
- **Type**: `boolean`
- **Description**: `redirect_on_update` is a boolean variable within the `GitHubAppResource` class that indicates whether the application should redirect users after an update. This variable is set to `True` by default, suggesting that redirection is enabled unless explicitly disabled.
- **Use**: It is used to control the behavior of the application regarding user redirection following updates.


---
### region 
- **Type**: `string`
- **Description**: The `region` variable is a string that specifies the geographical region associated with a `Developer` instance. It defaults to 'us', indicating that the developer is primarily based in the United States.
- **Use**: This variable is used to categorize or filter developers based on their geographical location.


---
### request_oauth_on_installation 
- **Type**: `boolean`
- **Description**: `request_oauth_on_installation` is a boolean attribute within the `GitHubAppResource` class that indicates whether OAuth authorization should be requested when the GitHub app is installed. This variable is set to `True` by default, suggesting that the app will prompt for OAuth permissions upon installation.
- **Use**: It is used to control the OAuth request behavior during the installation of a GitHub app.


---
### reserved_domains 
- **Type**: `list[NgrokReservedDomain]`
- **Description**: `reserved_domains` is a global variable that holds a list of `NgrokReservedDomain` instances, which represent domains reserved for a developer's use. Each `NgrokReservedDomain` contains details such as the domain type, subdomain, and status, allowing for organized management of domain resources.
- **Use**: This variable is used to store and manage the domains that a developer has reserved for their applications.


---
### reserved_tcp_address 
- **Type**: `NgrokReservedTcpAddress | None`
- **Description**: The `reserved_tcp_address` variable is an optional attribute of the `Developer` class that holds an instance of `NgrokReservedTcpAddress`, which represents a reserved TCP address for the developer's resources. This variable can be `None`, indicating that no reserved TCP address has been assigned.
- **Use**: It is used to store the TCP address reserved for the developer's application, if applicable.


---
### resource_name 
- **Type**: `str`
- **Description**: `resource_name` is a string variable that represents the name of a resource in the context of a developer's application. It is used to uniquely identify a resource within various configurations and requests.
- **Use**: This variable is utilized to specify the name of resources in different resource configuration classes.


---
### resources 
- **Type**: `list[DeveloperResource]`
- **Description**: The `resources` variable is a list that holds instances of `DeveloperResource`, which represent various resources associated with a developer. Each resource includes details such as the resource name, type, and specific configurations.
- **Use**: This variable is used to manage and store multiple resources that a developer can utilize within the application.


---
### secret_map 
- **Type**: `dict[str, str] | None`
- **Description**: `secret_map` is a dictionary that maps secret names (as strings) to their corresponding secret values (also as strings). It is used to store sensitive information securely, such as API keys or database credentials, which are necessary for the application to function properly.
- **Use**: This variable is used to manage and retrieve sensitive secrets required for various resource configurations.


---
### setup_url 
- **Type**: `str`
- **Description**: `setup_url` is a string variable that holds the URL used for setting up a GitHub application. It is part of the `GitHubAppResource` class, which encapsulates various configurations and properties related to a GitHub app.
- **Use**: This variable is used to specify the setup URL for the GitHub app during its configuration.


---
### signing_alg 
- **Type**: `string`
- **Description**: The `signing_alg` variable is a string that specifies the algorithm used for signing tokens in the `Auth0ApiCreateRequest` class. It defaults to 'RS256', which is a widely used algorithm for secure token signing.
- **Use**: This variable is used to define the signing algorithm for API requests when creating an Auth0 application.


---
### skip_consent_for_verifiable_first_party_clients 
- **Type**: `boolean`
- **Description**: The `skip_consent_for_verifiable_first_party_clients` variable is a boolean flag that indicates whether consent should be skipped for first-party clients that are verifiable. This variable is part of the `Auth0ApiCreateRequest` class, which is used to configure API settings in an Auth0 application.
- **Use**: It is used to determine if consent is required for verifiable first-party clients during API requests.


---
### ssl_verification_enabled 
- **Type**: `boolean`
- **Description**: The `ssl_verification_enabled` variable is a boolean flag that indicates whether SSL verification is enabled for the webhook configuration in the `GitHubAppWebhookConfig` class. By default, it is set to `True`, ensuring that SSL certificates are validated during communication.
- **Use**: This variable is used to control the SSL verification behavior when establishing secure connections for webhooks.


---
### token_endpoint_auth_method 
- **Type**: `string`
- **Description**: The `token_endpoint_auth_method` variable is a string attribute of the `Auth0SpaCreateAppRequest` class that specifies the authentication method used for the token endpoint. It is initialized with a default value of 'none', indicating that no specific authentication method is required.
- **Use**: This variable is used to define the authentication method for obtaining tokens in the context of creating an Auth0 Single Page Application.


---
### token_lifetime 
- **Type**: `int`
- **Description**: `token_lifetime` is an integer variable that specifies the duration, in seconds, for which a token is valid. It is set to a default value of 86400 seconds, which corresponds to 24 hours.
- **Use**: This variable is used to define the lifetime of tokens issued in the `Auth0ApiCreateRequest` class.


# Classes

---
### ApiResourceConfig 
- **Type**: `class`
- **Members**:
    - `resource_name`: A string representing the name of the API resource, defaulting to 'backend'.
    - `env`: A dictionary containing environment-specific configurations for the API resource.
- **Description**: The `ApiResourceConfig` class is a configuration model for API resources, inheriting from `BaseModel`. It defines the structure for specifying the name of the API resource and its associated environment configurations. This class is part of a larger system for managing various types of resources, providing a standardized way to define and access API-specific settings.
- **Inherits From**:
    - BaseModel


---
### Auth0ApiCreateRequest 
- **Type**: `class`
- **Members**:
    - `name`: A string representing the name of the API, with whitespace stripped and a minimum length of 1.
    - `identifier`: A string that serves as the unique identifier for the API.
    - `signing_alg`: A string representing the signing algorithm used, defaulting to 'RS256'.
    - `token_lifetime`: An integer representing the token lifetime in seconds, defaulting to 86400 (24 hours).
    - `skip_consent_for_verifiable_first_party_clients`: A boolean indicating whether to skip consent for verifiable first-party clients, defaulting to True.
    - `allow_offline_access`: A boolean indicating whether offline access is allowed, defaulting to True.
    - `enforce_policies`: A boolean indicating whether to enforce policies (RBAC), defaulting to True.
    - `include_email_in_tokens`: A boolean indicating whether to include email in tokens, defaulting to False.
    - `scopes`: A list of dictionaries representing the scopes for the API.
    - `allow_skip_consent`: A boolean indicating whether to allow skipping consent, defaulting to True.
    - `enable_permissions_in_token`: A boolean indicating whether to enable permissions in the token, defaulting to True.
- **Description**: The `Auth0ApiCreateRequest` class is a Pydantic model designed to facilitate the creation of an API request for Auth0. It includes various configuration options such as the API's name, identifier, signing algorithm, token lifetime, and several boolean flags to control consent and access policies. The class ensures that the API request is structured correctly with default values for many of its attributes, making it easier to manage API configurations in an Auth0 environment.
- **Inherits From**:
    - BaseModel


---
### Auth0M2MCreateRequest 
- **Type**: `class`
- **Members**:
    - `name`: A string representing the name of the M2M application, with whitespace stripped and a minimum length of 1.
    - `app_type`: A string indicating the type of application, defaulting to 'non_interactive'.
    - `logo_uri`: An optional string representing the URI of the application's logo.
    - `grant_types`: A list of strings specifying the grant types, defaulting to ['client_credentials'].
- **Description**: The `Auth0M2MCreateRequest` class is a Pydantic model used to define the structure and validation rules for creating a machine-to-machine (M2M) application request in Auth0. It includes fields for the application's name, type, logo URI, and grant types, with default values and constraints to ensure valid data is provided.
- **Inherits From**:
    - BaseModel


---
### Auth0SpaCreateAppRequest 
- **Type**: `class`
- **Members**:
    - `name`: The name of the application, with whitespace stripped and a minimum length of 1.
    - `app_type`: The type of application, defaulting to 'spa' (Single Page Application).
    - `callbacks`: A list of callback URLs for the application.
    - `allowed_logout_urls`: A list of URLs where users can be redirected after logging out.
    - `web_origins`: A list of allowed web origins for CORS.
    - `allowed_origins`: A list of allowed origins for CORS, defaulting to an empty list.
    - `initiate_login_uri`: The URI to initiate login, which is optional.
    - `oidc_conformant`: A boolean indicating if the application is OIDC conformant, defaulting to True.
    - `token_endpoint_auth_method`: The authentication method for the token endpoint, defaulting to 'none'.
    - `grant_types`: A list of grant types the application supports, defaulting to ['authorization_code', 'refresh_token', 'implicit'].
    - `organization_usage`: Specifies the organization usage policy, defaulting to 'require'.
    - `organization_require_behavior`: Specifies the behavior for organization requirement, defaulting to 'pre_login_prompt'.
- **Description**: The `Auth0SpaCreateAppRequest` class is a Pydantic model used to define the structure and validation rules for creating a Single Page Application (SPA) in Auth0. It includes various configuration options such as callback URLs, allowed logout URLs, web origins, and authentication methods. The class ensures that the application is OIDC conformant by default and supports multiple grant types. It also includes settings for organization usage and behavior, making it a comprehensive model for SPA configuration in Auth0.
- **Inherits From**:
    - BaseModel


---
### CDKResourceConfig 
- **Type**: `class`
- **Members**:
    - `resource_name`: A string representing the name of the resource, defaulting to 'cdk-stack'.
    - `execute`: A string representing the command or script to execute.
    - `env`: A dictionary containing environment variables for the resource.
- **Description**: The `CDKResourceConfig` class is a configuration model for a CDK (Cloud Development Kit) stack resource, inheriting from Pydantic's `BaseModel`. It defines the structure for specifying the resource name, the execution command, and the environment variables required for the resource. This class is used to encapsulate the configuration details necessary for deploying or managing a CDK stack within a cloud infrastructure.
- **Inherits From**:
    - BaseModel


---
### ContentServicesResource 
- **Type**: `class`
- **Members**:
    - `modal_environment`: A string representing the environment for the modal.
    - `secrets`: A list of ModalSecretResource objects associated with the content services.
- **Description**: The ContentServicesResource class is a data model that represents a resource configuration for content services within a modal environment. It includes attributes for specifying the environment and a list of secrets, which are instances of the ModalSecretResource class. This class is used to encapsulate the necessary configuration details for managing content services in a structured manner.
- **Inherits From**:
    - BaseModel


---
### DatabaseResource 
- **Type**: `class`
- **Members**:
    - `db_name`: The name of the database.
    - `host_address`: The address of the database host.
    - `user_name`: The username for database authentication.
    - `password`: The password for database authentication.
    - `db_url`: A computed property that returns the database URL for synchronous connections.
    - `async_db_url`: A computed property that returns the database URL for asynchronous connections.
- **Description**: The `DatabaseResource` class is a Pydantic model that represents the configuration details required to connect to a database. It includes attributes for the database name, host address, username, and password. Additionally, it provides computed properties to generate the database connection URLs for both synchronous and asynchronous connections using PostgreSQL.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### DatabaseResource.async_db_url
The `async_db_url` function constructs and returns a PostgreSQL database connection URL using the asyncpg driver with the provided database credentials.
- **Inputs**:
    - `self`: An instance of the `DatabaseResource` class containing database connection details such as `db_name`, `host_address`, `user_name`, and `password`.
- **Control Flow**:
    - The function uses an f-string to format a connection URL string for a PostgreSQL database using the asyncpg driver.
    - It accesses the `user_name`, `password`, `host_address`, and `db_name` attributes from the `self` object to construct the URL.
- **Output**:
    - A string representing the PostgreSQL connection URL using the asyncpg driver.


---
#### DatabaseResource.db_url
The `db_url` function constructs and returns a PostgreSQL database connection URL using the provided user credentials and database details.
- **Inputs**:
    - `self`: An instance of the `DatabaseResource` class, which contains attributes like `user_name`, `password`, `host_address`, and `db_name`.
- **Control Flow**:
    - The function accesses the `user_name`, `password`, `host_address`, and `db_name` attributes from the `self` object, which is an instance of the `DatabaseResource` class.
    - It constructs a database connection URL string in the format `postgresql+psycopg2://{user_name}:{password}@{host_address}/{db_name}`.
    - The constructed URL string is returned as the output of the function.
- **Output**:
    - A string representing the PostgreSQL database connection URL.



---
### DatabaseResourceConfig 
- **Type**: `class`
- **Members**:
    - `resource_name`: A string representing the name of the resource, defaulting to 'database'.
    - `env`: A dictionary containing environment-specific configurations.
    - `secret_map`: An optional dictionary mapping secret keys to their corresponding values.
- **Description**: The `DatabaseResourceConfig` class is a configuration model for database resources, inheriting from `BaseModel`. It includes attributes for specifying the resource name, environment configurations, and an optional mapping of secrets. This class is designed to facilitate the management and organization of database-related settings within a larger application context.
- **Inherits From**:
    - BaseModel


---
### Developer 
- **Type**: `class`
- **Members**:
    - `full_name`: The full name of the developer.
    - `email`: The email address of the developer.
    - `region`: The region associated with the developer, defaulting to 'us'.
    - `reserved_domains`: A list of NgrokReservedDomain objects associated with the developer.
    - `reserved_tcp_address`: An optional NgrokReservedTcpAddress object for the developer.
    - `auth0_webapp`: An optional dictionary containing Auth0 web application configuration.
    - `auth0_api`: An optional dictionary containing Auth0 API configuration.
    - `auth0_m2m`: An optional dictionary containing Auth0 machine-to-machine configuration.
    - `github_app`: An optional GitHubAppResource object associated with the developer.
    - `database`: An optional DatabaseResource object associated with the developer.
    - `resources`: A list of DeveloperResource objects associated with the developer.
    - `s3_bucket_name`: A computed property that returns a sanitized S3 bucket name based on the developer's full name.
    - `sanitized_full_name`: A computed property that returns a sanitized version of the developer's full name.
- **Description**: The Developer class is a data model that represents a developer's profile, including personal information such as full name and email, as well as various resources and configurations associated with the developer. It includes fields for managing reserved domains, TCP addresses, Auth0 configurations, GitHub applications, databases, and other developer resources. The class also provides computed properties to generate a sanitized S3 bucket name and a sanitized version of the developer's full name, ensuring compatibility with naming conventions.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### Developer.s3_bucket_name
The `s3_bucket_name` function generates a standardized S3 bucket name based on the developer's full name.
- **Inputs**:
    - None
- **Control Flow**:
    - The function accesses the `full_name` attribute of the `Developer` class instance.
    - It converts the `full_name` to lowercase, removes spaces, and strips any leading or trailing whitespace.
    - It appends the string '-asset-dropzone' to the processed `full_name`.
    - The function returns the resulting string as the S3 bucket name.
- **Output**:
    - A string representing the S3 bucket name, formatted as the developer's full name in lowercase without spaces, followed by '-asset-dropzone'.


---
#### Developer.sanitized_full_name
The `sanitized_full_name` function converts a developer's full name into a sanitized, lowercase, hyphen-separated string suitable for use in URLs or identifiers.
- **Inputs**:
    - `self`: An instance of the Developer class, which contains the full_name attribute to be sanitized.
- **Control Flow**:
    - The function accesses the `full_name` attribute of the `self` object, which is expected to be a string.
    - It converts the `full_name` to lowercase and replaces spaces with hyphens.
    - It uses a regular expression to remove any characters that are not lowercase letters, digits, or hyphens.
    - The sanitized string is stored in the `sanitized_name` variable.
    - The function returns the `sanitized_name`.
- **Output**:
    - A string that is a sanitized version of the developer's full name, containing only lowercase letters, digits, and hyphens.



---
### DeveloperResource 
- **Type**: `class`
- **Members**:
    - `resource_name`: A string representing the name of the developer resource.
    - `resource_type`: An instance of DeveloperResourceType indicating the type of the developer resource.
    - `resource`: A dictionary containing additional details or configurations for the developer resource.
- **Description**: The DeveloperResource class is a data model that represents a resource used by developers, characterized by a name, type, and additional configuration details. It inherits from BaseModel, which provides data validation and serialization capabilities. The class is designed to encapsulate information about various types of developer resources, such as web applications, APIs, or databases, as defined by the DeveloperResourceType enumeration.
- **Inherits From**:
    - BaseModel


---
### DeveloperResourceType 
- **Type**: `enum.Enum`
- **Members**:
    - `WEB_APP`: Represents a web application resource type.
    - `API`: Represents an API resource type.
    - `M2M`: Represents a machine-to-machine resource type.
    - `DB`: Represents a database resource type.
    - `GITHUB_APP`: Represents a GitHub application resource type.
    - `ASSET_ONBOARDING_LAMBDA`: Represents an asset onboarding lambda resource type.
    - `METRICS_LAMBDA`: Represents a metrics lambda resource type.
    - `S3_BUCKET`: Represents an S3 bucket resource type.
    - `CDK_STACK`: Represents a CDK stack resource type.
    - `CONTENT_SERVICES`: Represents a content services resource type.
    - `DOCKER`: Represents a Docker resource type.
- **Description**: The `DeveloperResourceType` class is an enumeration that defines various types of developer resources, such as web applications, APIs, databases, and cloud services like AWS Lambda and S3 buckets. Each member of the enumeration represents a specific type of resource that a developer might work with or manage in a software development environment.
- **Inherits From**:
    - enum.Enum


---
### DomainStatus 
- **Type**: `enum.Enum`
- **Members**:
    - `CREATED`: Represents a domain status where the domain has been successfully created.
    - `FAILED`: Represents a domain status where the domain creation has failed.
- **Description**: The `DomainStatus` class is an enumeration that defines the possible statuses for a domain, specifically indicating whether a domain has been successfully created or if the creation process has failed. This class is used to standardize the representation of domain statuses within the application, providing a clear and consistent way to handle domain state information.
- **Inherits From**:
    - enum.Enum


---
### DomainType 
- **Type**: `enum.Enum`
- **Members**:
    - `WEBAPP`: Represents a web application domain type.
    - `API`: Represents an API domain type.
    - `TCP`: Represents a TCP domain type.
- **Description**: The `DomainType` class is an enumeration that defines different types of domains that can be used within the application. It includes three specific domain types: WEBAPP, API, and TCP, each represented as a string value. This enumeration is useful for categorizing and managing different domain types in a consistent manner across the application.
- **Inherits From**:
    - enum.Enum


---
### GitHubAppPermissionsConfig 
- **Type**: `class`
- **Members**:
    - `repository_permissions`: A dictionary mapping repository permission names to their access levels.
    - `organization_permissions`: A dictionary mapping organization permission names to their access levels.
    - `account_permissions`: A dictionary mapping account permission names to their access levels.
- **Description**: The `GitHubAppPermissionsConfig` class is a Pydantic model that defines the configuration for permissions associated with a GitHub App. It includes three dictionaries: `repository_permissions`, `organization_permissions`, and `account_permissions`, each mapping permission names to their respective access levels, which can be 'read-only', 'read-write', or 'no-access'. This class is used to specify and validate the permissions required by a GitHub App for different scopes within a GitHub organization or account.
- **Inherits From**:
    - BaseModel


---
### GitHubAppResource 
- **Type**: `class`
- **Members**:
    - `app_name`: The name of the GitHub App.
    - `app_id`: The unique identifier for the GitHub App, which can be None.
    - `client_id`: The client ID for the GitHub App, which can be None.
    - `client_secret`: The client secret for the GitHub App, which can be None.
    - `homepage_url`: The homepage URL of the GitHub App.
    - `callback_url`: The callback URL for the GitHub App.
    - `request_oauth_on_installation`: Indicates if OAuth should be requested upon installation, default is True.
    - `enable_device_flow`: Indicates if device flow is enabled, default is True.
    - `setup_url`: The setup URL for the GitHub App, which can be None.
    - `redirect_on_update`: Indicates if redirection should occur on update, default is True.
    - `webhook`: Configuration for the GitHub App's webhook.
    - `permissions`: Configuration for the GitHub App's permissions.
    - `subscribed_events`: List of events the GitHub App is subscribed to.
    - `public_in_marketplace`: Indicates if the app is public in the marketplace, default is False.
    - `private_key_pem_path`: Path to the private key PEM file, which can be None.
    - `base64_private_key_pem`: Base64 encoded private key PEM, which can be None.
- **Description**: The `GitHubAppResource` class is a Pydantic model that represents the configuration and properties of a GitHub App. It includes various attributes such as the app's name, ID, client credentials, URLs, and settings related to OAuth, device flow, and marketplace visibility. Additionally, it holds configurations for webhooks and permissions, as well as a list of events the app is subscribed to. This class is designed to encapsulate all necessary information for managing a GitHub App within a software system.
- **Inherits From**:
    - BaseModel


---
### GitHubAppWebhookConfig 
- **Type**: `class`
- **Members**:
    - `webhook_url`: A string representing the URL to which the webhook will send payloads.
    - `webhook_secret`: An optional string used to secure the webhook payloads.
    - `ssl_verification_enabled`: A boolean indicating if SSL verification is enabled, defaulting to True.
- **Description**: The `GitHubAppWebhookConfig` class is a Pydantic model that defines the configuration for a GitHub App webhook. It includes the URL where the webhook will send payloads, an optional secret for securing the payloads, and a flag to enable or disable SSL verification. This class is used to ensure that the webhook configuration adheres to the expected structure and data types.
- **Inherits From**:
    - BaseModel


---
### LambdaResourceConfig 
- **Type**: `class`
- **Members**:
    - `resource_name`: A string representing the name of the Lambda resource.
    - `env`: A dictionary containing environment variables for the Lambda resource.
    - `secret_map`: A dictionary mapping secret names to their corresponding values for the Lambda resource.
- **Description**: The `LambdaResourceConfig` class is a data model that defines the configuration for a Lambda resource. It includes attributes for specifying the resource's name, environment variables, and a mapping of secret names to their values. This class is useful for managing and organizing the configuration details required to deploy and operate a Lambda function within a cloud environment.
- **Inherits From**:
    - BaseModel


---
### ModalSecretResource 
- **Type**: `class`
- **Members**:
    - `resource_name`: A string representing the name of the resource.
    - `env`: A dictionary containing environment-specific configurations for the resource.
- **Description**: The `ModalSecretResource` class is a data model that represents a secret resource with a specific name and associated environment configurations. It is used to encapsulate the details of a resource that requires secret management, such as environment variables or other sensitive information, within a modal context. This class inherits from `BaseModel`, which provides validation and serialization capabilities.
- **Inherits From**:
    - BaseModel


---
### NgrokReservedDomain 
- **Type**: `class`
- **Members**:
    - `domain_type`: Specifies the type of domain, using the DomainType enum.
    - `subdomain`: Holds the subdomain part of the reserved domain.
    - `domain`: Stores the main domain name.
    - `description`: Provides a description of the reserved domain.
    - `region`: Indicates the region for the domain, defaulting to 'us'.
    - `status`: Represents the current status of the domain using the DomainStatus enum.
    - `metadata`: Contains optional metadata as a dictionary.
    - `domain_url`: A computed property that returns the full URL of the domain.
- **Description**: The NgrokReservedDomain class is a Pydantic model that represents a reserved domain in the Ngrok system. It includes attributes for the domain type, subdomain, main domain, description, region, status, and optional metadata. The class also provides a computed property, domain_url, which constructs the full URL of the domain using the domain attribute. This class is useful for managing and storing information about domains reserved through Ngrok.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### NgrokReservedDomain.domain_url
The `domain_url` function constructs a URL string using the domain attribute of the `NgrokReservedDomain` class.
- **Inputs**:
    - None
- **Control Flow**:
    - The function is a computed property of the `NgrokReservedDomain` class, meaning it is accessed like an attribute but computed on-the-fly.
    - It returns a formatted string that combines the 'https://' prefix with the `domain` attribute of the `NgrokReservedDomain` instance.
- **Output**:
    - A string representing the full URL of the domain, prefixed with 'https://'.



---
### NgrokReservedTcpAddress 
- **Type**: `class`
- **Members**:
    - `address`: A string representing the TCP address.
    - `description`: A string providing a description of the TCP address.
    - `region`: A string indicating the region, defaulting to 'us'.
    - `status`: An instance of DomainStatus indicating the status of the domain.
    - `metadata`: An optional dictionary for additional metadata.
    - `address_url`: A computed property that returns the TCP address as a URL.
- **Description**: The `NgrokReservedTcpAddress` class is a Pydantic model that represents a reserved TCP address in the Ngrok system. It includes attributes for the address, description, region, status, and optional metadata. The class also provides a computed property `address_url` that formats the TCP address into a URL string prefixed with 'tcp://'. This class is useful for managing and representing TCP addresses reserved through Ngrok, with built-in validation and default values for certain fields.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### NgrokReservedTcpAddress.address_url
The `address_url` function constructs a TCP URL using the address attribute of the `NgrokReservedTcpAddress` class.
- **Inputs**:
    - `self`: An instance of the `NgrokReservedTcpAddress` class, which contains the `address` attribute used to construct the URL.
- **Control Flow**:
    - The function is a computed property method within the `NgrokReservedTcpAddress` class.
    - It returns a formatted string that combines the 'tcp://' prefix with the `address` attribute of the instance.
- **Output**:
    - A string representing the TCP URL constructed from the instance's address attribute.



---
### WebAppResourceConfig 
- **Type**: `class`
- **Members**:
    - `resource_name`: The name of the web application resource, defaulting to 'webapp-frontend'.
    - `setup_str`: A string representing the setup configuration for the web application.
    - `vite_config`: A dictionary containing the Vite configuration settings for the web application.
    - `env`: A dictionary representing the environment variables for the web application.
- **Description**: The `WebAppResourceConfig` class is a configuration model for a web application resource, inheriting from `BaseModel`. It defines the essential configuration parameters such as the resource name, setup string, Vite configuration, and environment variables necessary for setting up and managing a web application frontend. This class provides a structured way to handle configuration data for web applications, ensuring consistency and ease of use.
- **Inherits From**:
    - BaseModel


