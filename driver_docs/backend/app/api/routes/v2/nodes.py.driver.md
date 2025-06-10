# Purpose
This Python file is a FastAPI-based module that defines a set of RESTful API endpoints for managing "nodes" within a system. The code provides specific functionality for listing, creating, and updating nodes, which are likely entities related to a versioning system, as indicated by the relationships with `Version` and `PrimaryAsset` models. The endpoints are part of a broader API structure, as suggested by the use of a shared `router` object and the import of utility functions for query filtering and sorting. The endpoints are designed to ensure that operations are performed within the context of a user's organization, enforcing access control by checking the organization ID associated with the `PrimaryAsset`.

The file defines three main API endpoints: a GET endpoint to list nodes with pagination and filtering capabilities, a POST endpoint to create a new node, and a PUT endpoint to update an existing node. Each endpoint uses SQLAlchemy and SQLModel to interact with the database, leveraging ORM features like `selectinload` for efficient data retrieval. The endpoints also utilize FastAPI's dependency injection to handle request data and session management, ensuring that operations are performed within a valid user session. The code is structured to be part of a larger application, likely serving as a backend service for a web application or API client that requires node management capabilities.
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
### create_node 
The `create_node` function creates a new node in the database after verifying that the specified version belongs to the user's organization.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to interact with the database.
    - `user`: A `UserToken` object representing the authenticated user making the request.
    - `payload`: A `NodeCreate` object containing the data required to create a new node, including the version ID and relative path.
- **Control Flow**:
    - The function begins by executing a database query to select a `Version` that matches the `version_id` from the `payload` and belongs to the user's organization.
    - If no such version is found, an `HTTPException` with a 404 status code is raised, indicating that the version is not found or the user is not authorized.
    - If the version is found, a new `Node` object is created using the `version_id` and `relative_path` from the `payload`.
    - The new node is added to the session, the session is committed to save the changes, and the node is refreshed to update it with any database-generated values.
    - Finally, the newly created node is returned.
- **Output**:
    - The function returns the newly created `Node` object.


---
### list_nodes 
The `list_nodes` function retrieves a paginated list of nodes associated with a user's organization, applying any specified filters and sorting.
- **Inputs**:
    - `request`: An instance of `Request` containing query parameters for filtering the nodes.
    - `session`: An instance of `CurrentSession` used to execute database queries.
    - `user`: An instance of `UserToken` representing the authenticated user, used to filter nodes by organization.
    - `pagination`: An instance of `Pagination` containing pagination and sorting information for the query.
- **Control Flow**:
    - Constructs a SQL query to select `Node` objects, joining with `Version` and `PrimaryAsset` tables, and filters by the user's organization ID.
    - Converts query parameters from the request into a dictionary and applies them as filters to the query using `apply_filters_to_query`.
    - Creates a count query to determine the total number of nodes matching the filters and executes it to get the total count.
    - Applies sorting to the query based on the pagination information using `apply_sorting_to_query`.
    - Executes the final query to retrieve the list of nodes and stores the results.
    - Returns a `ListWithCount` object containing the list of nodes and the total count.
- **Output**:
    - A `ListWithCount` object containing the list of `Node` objects and the total count of nodes matching the query.


---
### update_node 
The `update_node` function updates a node's details in the database if it belongs to the user's organization.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to interact with the database.
    - `user`: A `UserToken` object representing the authenticated user making the request.
    - `node_id`: A `UUID` representing the unique identifier of the node to be updated, provided as a path parameter.
    - `payload`: A `NodeUpdate` object containing the new data for the node, provided in the request body.
- **Control Flow**:
    - The function begins by querying the database to fetch the node with the specified `node_id` and checks if it belongs to the user's organization by joining with `Version` and `PrimaryAsset` tables.
    - If the node is not found or does not belong to the user's organization, an `HTTPException` with a 404 status code is raised.
    - If the `relative_path` attribute in the `payload` is not `None`, the node's `relative_path` is updated with the new value.
    - The updated node is added to the session, the session is committed to save changes, and the node is refreshed to reflect the latest state from the database.
    - Finally, the updated node is returned.
- **Output**:
    - The function returns the updated `Node` object after successfully applying the changes.


