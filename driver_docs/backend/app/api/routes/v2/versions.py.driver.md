# Purpose
This Python file is a FastAPI-based module that defines a set of RESTful API endpoints for managing "Version" entities within an application. The code provides a focused functionality, specifically handling the creation, retrieval, and updating of version records associated with primary assets. The endpoints are designed to ensure that operations are performed within the context of a user's organization, leveraging user authentication and authorization through the `UserToken`. The module uses SQLAlchemy and SQLModel for database interactions, employing ORM techniques to query and manipulate data. Key components include the `list_versions` endpoint for retrieving a paginated list of versions, the `create_version` endpoint for adding new version records, and the `update_version` endpoint for modifying existing versions. Each endpoint is equipped with input validation and error handling to ensure robust API behavior.

The code is structured as a collection of API route handlers, making it suitable for integration into a larger FastAPI application. It defines public APIs that can be accessed by clients to interact with version data, with each endpoint returning structured responses modeled by Pydantic schemas. The use of utility functions like `apply_filters_to_query` and `apply_sorting_to_query` indicates a modular approach to query customization, enhancing the flexibility and reusability of the code. Overall, this file serves as a critical component of an API layer, facilitating version management in a multi-tenant environment where data access is scoped to the user's organization.
# Imports and Dependencies

---
- `uuid`
- `database.models_v2`
- `fastapi`
- `sqlalchemy.orm`
- `sqlmodel`
- `app.api.auth`
- `app.api.routes.v2.query_utils`
- `app.api.routes.v2.router`
- `app.api.routes.v2.schemas`
- `app.api.session`


# Functions

---
### create_version 
The `create_version` function creates a new version entry in the database after verifying that the primary asset belongs to the user's organization.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to interact with the database.
    - `user`: A `UserToken` object representing the authenticated user making the request.
    - `payload`: A `VersionCreate` object containing the data required to create a new version, passed in the request body.
- **Control Flow**:
    - The function starts by executing a database query to check if the primary asset specified in the payload belongs to the user's organization.
    - If the primary asset is not found or does not belong to the user's organization, an HTTP 404 exception is raised with the message 'Primary asset not found'.
    - If the primary asset is valid, a new `Version` object is created using the data from the payload.
    - The new version is added to the session and committed to the database.
    - The session is refreshed to ensure the new version object is updated with any database-generated values.
    - The newly created version object is returned.
- **Output**:
    - The function returns the newly created `Version` object after it has been added to the database.


---
### list_versions 
The `list_versions` function retrieves a paginated list of version details associated with a user's organization, applying any specified filters and sorting.
- **Inputs**:
    - `request`: An instance of `Request` containing query parameters for filtering the versions.
    - `session`: An instance of `CurrentSession` used to execute database queries.
    - `user`: An instance of `UserToken` representing the authenticated user, used to filter versions by organization.
    - `pagination`: An instance of `Pagination` containing pagination and sorting information for the query.
- **Control Flow**:
    - Constructs a SQL query to select `Version` records joined with `PrimaryAsset`, filtered by the user's organization ID.
    - Loads related data for each version using `selectinload` for `root_node`, `primary_asset`, and `creator`.
    - Converts request query parameters into a dictionary and applies them as filters to the query using `apply_filters_to_query`.
    - Creates a count query to determine the total number of filtered versions and executes it to get the count.
    - Applies sorting to the query based on the pagination information using `apply_sorting_to_query`.
    - Executes the final query to retrieve the list of versions and stores the results.
    - Returns a `ListWithCount` object containing the list of versions and the total count.
- **Output**:
    - A `ListWithCount` object containing the list of `VersionDetailRead` objects and the total count of versions matching the query.


---
### update_version 
The `update_version` function updates the display name of a specific version if it belongs to the user's organization.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to interact with the database.
    - `user`: A `UserToken` object representing the authenticated user making the request.
    - `version_id`: A `UUID` representing the unique identifier of the version to be updated, provided as a path parameter.
    - `payload`: A `VersionUpdate` object containing the new data for the version, provided in the request body.
- **Control Flow**:
    - The function begins by executing a database query to select the `Version` object that matches the given `version_id` and belongs to the organization of the authenticated user.
    - If no such version is found, an `HTTPException` with a 404 status code is raised, indicating that the version was not found.
    - If the version is found, its `display_name` attribute is updated with the value from the `payload`.
    - The updated version is added to the session, and the session is committed to save the changes to the database.
    - The session is refreshed to ensure the returned version object is up-to-date with the database.
    - Finally, the updated version object is returned.
- **Output**:
    - The function returns the updated `Version` object after successfully updating its display name in the database.


