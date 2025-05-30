# Purpose
This Python file defines a GraphQL API using the Strawberry library, focusing on operations related to organizations, document sets, codebase trees, and Git provider integrations. The file is structured as a collection of GraphQL query resolvers, each implemented as a method within the `Query` class, which is decorated with `@strawberry.type` to define the GraphQL schema. The primary purpose of this code is to facilitate interactions with an organization's data, such as retrieving organization details, accessing document sets, and listing connected Git providers and repositories. The code leverages various imported modules and functions to perform these operations, including access checks and data fetching from external sources like GitHub.

The file is designed to be part of a larger application, likely serving as a backend component that interfaces with a frontend client through GraphQL queries. It defines several public APIs that allow clients to query for specific data, such as organization information, document sets, and codebase trees. The code also includes utility functions, such as `is_code_content_requested`, to enhance query processing by determining if specific fields are requested. The integration with Git providers is facilitated through the `GithubAppInstallationsRepository` and `fetch_repos` functions, which manage and retrieve repository data. Overall, this file provides a focused set of functionalities centered around organizational data management and Git provider integration within a GraphQL API context.
# Imports and Dependencies

---
- `logging`
- `datetime`
- `strawberry`
- `app.api.routes.legacy.api_types`
- `app.api.routes.legacy.document_set`
- `app.api.routes.legacy.orm_ops`
- `app.api.routes.legacy.scalars`
- `app.api.routes.legacy.tree`
- `app.repositories.github_app_installations_repository`
- `app.utils.gh_ops`
- `graphql`
- `strawberry.types`
- `strawberry.types.nodes`


# Global Variables

---
### logger 
- **Type**: `logging.Logger`
- **Description**: The `logger` variable is an instance of the `Logger` class from the Python `logging` module. It is configured to use the name of the current module (`__name__`) as its logger name, which helps in identifying the source of log messages.
- **Use**: This variable is used to log informational messages, such as whether code content is requested, within the application.


# Classes

---
### MeResponse 
- **Type**: `class`
- **Members**:
    - `id`: Represents the unique identifier of the user.
- **Description**: The `MeResponse` class is a simple data structure used to encapsulate the response for a GraphQL query that retrieves information about the current user. It contains a single field, `id`, which is of type `ID` and represents the unique identifier of the user. This class is part of a larger GraphQL API implementation using the Strawberry library.


---
### OrganizationResult 
- **Type**: `dataclass`
- **Members**:
    - `id`: A string representing the unique identifier of the organization.
    - `name`: A string representing the name of the organization.
    - `display_name`: A string representing the display name of the organization.
    - `workspaces`: A list of strings representing the workspaces associated with the organization.
- **Description**: The `OrganizationResult` class is a data structure used to represent an organization within the system. It includes essential information such as the organization's unique identifier (`id`), its name (`name`), a display name (`display_name`), and a list of associated workspaces (`workspaces`). This class is likely used in the context of GraphQL queries to return organization-related data to clients.


---
### Query 
- **Type**: `class`
- **Members**:
    - `organization`: A method to retrieve organization details based on the user's context.
    - `documentSet`: A method to fetch a document set, ensuring access permissions and required parameters are provided.
    - `tree`: A method to retrieve the codebase tree for a given organization and version.
    - `me`: A method to return the current user's ID.
    - `connectedGitProviders`: A method to list configured Git providers for the user or organization.
    - `reposByGitProvider`: A method to fetch repositories from a specified Git provider, currently only supporting GitHub.
- **Description**: The `Query` class is a GraphQL query handler that provides various endpoints to interact with organizational data, document sets, codebase trees, user information, and Git provider configurations. It uses the `strawberry` library to define GraphQL fields and ensures proper access control and parameter validation for sensitive operations. The class supports fetching organization details, document sets, codebase trees, user information, connected Git providers, and repositories by Git provider, with a focus on GitHub integration.

**Methods**

---
#### Query.connectedGitProviders
The `connectedGitProviders` function returns a list of Git providers configured for a user's organization.
- **Inputs**:
    - `info`: An `Info` object that contains context about the GraphQL request, including the user and session information.
- **Control Flow**:
    - Initialize an empty list `providers` to store the configured Git providers.
    - Retrieve the current user from the `info.context.user`.
    - Create an instance of `GithubAppInstallationsRepository` using the session from `info.context.session`.
    - Check if there are any GitHub installations for the user's organization by calling `list_by_organization_id` with the user's organization ID.
    - If there are any installations, append a `GitProvider` object representing GitHub to the `providers` list.
    - Return the `providers` list.
- **Output**:
    - A list of `GitProvider` objects representing the Git providers configured for the user's organization.


---
#### Query.documentSet
The `documentSet` function retrieves a set of documents based on specified parameters, ensuring access permissions and optionally fetching code content.
- **Inputs**:
    - `info`: An instance of `Info` that contains context about the GraphQL request, including session and user information.
    - `nodeKind`: A `NodeType` that specifies the kind of node for which the document set is being requested.
    - `path`: An optional string representing the path to the document set; must not be `None`.
    - `primaryAssetId`: An optional `ID` representing the primary asset identifier; must not be `None`.
    - `versionId`: An optional `ID` representing the version identifier; must not be `None`.
- **Control Flow**:
    - Check if `path`, `versionId`, or `primaryAssetId` is `None` and raise a `GraphQLError` if any are `None`.
    - Retrieve the session from `info.context.session`.
    - Check access permissions using `check_access` with the session, organization ID, and primary asset ID; raise a `GraphQLError` if access is denied.
    - Determine if code content is requested by calling `is_code_content_requested(info)`.
    - Log whether code content is requested using the logger.
    - Call `get_document_set` with the provided parameters and return its result.
- **Output**:
    - Returns a `DocumentSet` object that contains the requested documents.


---
#### Query.me
The `me` function returns a `MeResponse` object containing the ID of the current user.
- **Inputs**:
    - `info`: An `Info` object that provides context about the GraphQL request, including the current user.
- **Control Flow**:
    - Retrieve the current user from the `info.context.user` attribute.
    - Create and return a `MeResponse` object with the user's ID as the `id` attribute.
- **Output**:
    - A `MeResponse` object containing the ID of the current user.


---
#### Query.organization
The `organization` function returns an `OrganizationResult` object containing the organization ID, name, display name, and an empty list of workspaces based on the user's context.
- **Inputs**:
    - `info`: An `Info` object that contains the context of the GraphQL request, including user information.
    - `id`: A string representing the organization ID, although it is not used in the function body.
- **Control Flow**:
    - The function directly returns an `OrganizationResult` object without any conditional logic or iterations.
    - The `OrganizationResult` is constructed using the organization ID and display name from the `info.context.user` object, and an empty list for workspaces.
- **Output**:
    - An `OrganizationResult` object with the organization's ID, name, display name, and an empty list of workspaces.


---
#### Query.reposByGitProvider
The `reposByGitProvider` function retrieves a list of Git repositories for a specified provider, currently only supporting GitHub.
- **Inputs**:
    - `info`: An `Info` object containing context about the GraphQL request, including user and session information.
    - `provider`: A string specifying the name of the Git provider, which must be 'github'.
- **Control Flow**:
    - Initialize an empty list `repos` to store the resulting GitRepository objects.
    - Retrieve the user and session from the `info.context`.
    - Check if the `provider` is not 'github', and if so, raise a `NotImplementedError`.
    - Call `fetch_repos` with the session and user's organization ID to get a list of repositories.
    - Iterate over the fetched repositories, creating a `GitRepository` object for each, and append it to the `repos` list.
    - Return the list of `GitRepository` objects.
- **Output**:
    - A list of `GitRepository` objects representing the repositories fetched from the specified provider.


---
#### Query.tree
The `tree` function retrieves a list of `FlatNode` objects representing the codebase tree for a given organization and version.
- **Inputs**:
    - `info`: An `Info` object containing the context of the GraphQL request, including session and user information.
    - `codebaseId`: An optional `ID` representing the codebase identifier.
    - `workspaceId`: An optional `ID` representing the workspace identifier.
    - `versionId`: An optional `ID` representing the version identifier of the codebase.
- **Control Flow**:
    - Retrieve the session and user from the `info` context.
    - Commented out code suggests there was previously an access check for the primary asset, but it is currently not enforced.
    - Call the `get_codebase_tree` function with the session, organization ID, and version ID to retrieve the codebase tree.
- **Output**:
    - A list of `FlatNode` objects representing the structure of the codebase tree.



# Functions

---
### has_content_field 
The `has_content_field` function checks if a list of GraphQL `Selection` objects contains a 'content' field nested under a 'code' field.
- **Inputs**:
    - `fields`: A list of `Selection` objects representing fields in a GraphQL query.
- **Control Flow**:
    - Iterate over each `field` in the `fields` list.
    - Check if the `field` has the name 'code' and contains a subfield with the name 'content'.
    - If such a subfield is found, return `True`.
    - If the `field` has nested selections, recursively call `has_content_field` on these selections.
    - If any recursive call returns `True`, return `True`.
    - If no 'content' field is found under a 'code' field, return `False`.
- **Output**:
    - A boolean value indicating whether a 'content' field is found under a 'code' field in the given selections.


---
### is_code_content_requested 
The function `is_code_content_requested` checks if a GraphQL query requests the 'content' field under 'code' by recursively examining the query's selected fields.
- **Inputs**:
    - `info`: An instance of `Info` from the Strawberry GraphQL library, which contains the selected fields of a GraphQL query.
- **Control Flow**:
    - Define a nested function `has_content_field` that takes a list of `Selection` objects as input.
    - Iterate over each `field` in the provided list of `Selection` objects.
    - Check if the `field` name is 'code' and if any of its subfields have the name 'content'.
    - If the above condition is met, return `True`.
    - If the `field` has nested selections, recursively call `has_content_field` on these selections.
    - If none of the conditions are met, return `False`.
    - Call `has_content_field` with `info.selected_fields` and return its result.
- **Output**:
    - A boolean value indicating whether the 'content' field under 'code' is requested in the query.


