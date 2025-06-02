# Purpose
This Python file is a FastAPI-based module that provides RESTful API endpoints for managing "tags" within an application. The code defines three main endpoints: listing tags, updating a tag, and creating a new tag. These endpoints are part of a broader API structure, as indicated by the use of a router from the `app.api.routes.v2.router` module. The endpoints are designed to interact with a database model `Tag`, which is likely defined in the `database.models_v1` module. The code leverages SQLModel for database interactions, using SQL queries to select, update, and insert tag records.

The file is structured to handle HTTP requests and responses, with each endpoint function decorated with HTTP method decorators (`@router.get`, `@router.put`, `@router.post`). The endpoints utilize dependency injection to access the current session and user information, ensuring that operations are performed within the context of the authenticated user's organization. The code also includes utility functions for query filtering, sorting, and pagination, which are applied to the tag listing endpoint. This module is intended to be part of a larger application, providing a specific set of functionalities related to tag management, and it defines a public API for external clients to interact with the tag data.
# Imports and Dependencies

---
- `uuid`
- `database.models_v1`
- `fastapi`
- `sqlmodel`
- `app.api.auth`
- `app.api.routes.v2.query_utils`
- `app.api.routes.v2.router`
- `app.api.routes.v2.schemas`
- `app.api.session`


# Functions

---
### create_tag 
The `create_tag` function creates a new tag in the database using the provided session, user, and payload data.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to interact with the database.
    - `user`: An instance of `UserToken` representing the authenticated user, providing user and organization context.
    - `payload`: An instance of `TagCreate` containing the data required to create a new tag, such as name and hex color.
- **Control Flow**:
    - A new `Tag` object is instantiated with the name, organization ID, hex color, and user information from the `payload` and `user` arguments.
    - The new tag is added to the database session using `session.add(new_tag)`.
    - The session is committed to save the new tag to the database with `session.commit()`.
    - The session is refreshed to update the `new_tag` object with any changes made during the commit, such as auto-generated fields like ID.
    - The newly created `Tag` object is returned.
- **Output**:
    - The function returns a `TagRead` object representing the newly created tag.


---
### list_tags 
The `list_tags` function retrieves and returns a paginated list of tags associated with a user's organization, applying any specified filters and sorting.
- **Inputs**:
    - `request`: An instance of `Request` containing query parameters for filtering the tags.
    - `session`: An instance of `CurrentSession` used to execute database queries.
    - `user`: An instance of `UserToken` representing the authenticated user, used to filter tags by organization.
    - `pagination`: An instance of `Pagination` containing pagination and sorting information for the query.
- **Control Flow**:
    - Initialize a query to select tags where the `organization_id` matches the user's organization ID.
    - Convert the request's query parameters into a dictionary of filters.
    - Apply these filters to the query using `apply_filters_to_query`.
    - Create a count query to determine the total number of tags after filtering.
    - Execute the count query to get the total count of tags.
    - Apply sorting to the query based on the pagination information using `apply_sorting_to_query`.
    - Execute the final query to retrieve the list of tags.
    - Return a `ListWithCount` object containing the list of tags and the total count.
- **Output**:
    - A `ListWithCount` object containing the list of `TagDetailRead` objects and the total count of tags after filtering and sorting.


---
### update_tag 
The `update_tag` function updates an existing tag's details in the database if it belongs to the user's organization.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to interact with the database.
    - `user`: A `UserToken` object representing the authenticated user making the request.
    - `tag_id`: A `UUID` representing the unique identifier of the tag to be updated, provided as a path parameter.
    - `payload`: A `TagCreate` object containing the new data for the tag, provided in the request body.
- **Control Flow**:
    - The function begins by querying the database to find a tag with the specified `tag_id` that also belongs to the user's organization.
    - If no such tag is found, an `HTTPException` with a 404 status code is raised, indicating the tag was not found.
    - If the `payload` contains a new name, hex color, or type, these fields are updated on the tag object.
    - The `updated_by` field of the tag is set to the `user_id` of the current user.
    - The updated tag is added to the session, and the session is committed to save changes to the database.
    - The session is refreshed to ensure the tag object is up-to-date with the database state.
    - Finally, the updated tag object is returned.
- **Output**:
    - The function returns a `TagRead` object representing the updated tag.


