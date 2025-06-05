# Purpose
This Python file is part of a web application built using the FastAPI framework, and it defines two API endpoints for managing `PrimaryAssetTag` resources. The file is structured as a module that is likely part of a larger application, as indicated by its use of imports from other parts of the application, such as `app.api.auth`, `app.api.routes.v2.router`, and `app.api.session`. The primary functionality provided by this file is the creation and deletion of `PrimaryAssetTag` objects, which are likely used to associate tags with primary assets in a database. The endpoints are defined using FastAPI's routing capabilities, with the `@router.post` and `@router.delete` decorators specifying the HTTP methods and paths.

The `delete_primary_asset_tag` function handles DELETE requests to remove a `PrimaryAssetTag` based on a given `primary_asset_id` and `tag_id`, ensuring that the tag belongs to the user's organization. It raises an HTTP 404 error if the tag is not found or the user is not authorized. The `create_primary_asset_tag` function handles POST requests to create a new `PrimaryAssetTag`, using data provided in the request body. Both functions interact with a database session to perform their operations, utilizing SQLModel for ORM capabilities. The file defines a narrow scope of functionality focused on managing `PrimaryAssetTag` entities, and it provides a clear API for these operations, making it suitable for integration into a larger system that requires asset tagging capabilities.
# Imports and Dependencies

---
- `uuid`
- `database.models_v2`
- `fastapi`
- `sqlmodel`
- `app.api.auth`
- `app.api.routes.v2.router`
- `app.api.routes.v2.schemas`
- `app.api.session`


# Functions

---
### create_primary_asset_tag 
The function `create_primary_asset_tag` creates and persists a new `PrimaryAssetTag` in the database using the provided session and payload data.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to interact with the database.
    - `user`: A `UserToken` object representing the authenticated user making the request.
    - `payload`: A `PrimaryAssetTagCreate` object containing the data required to create a new `PrimaryAssetTag`, provided in the request body.
- **Control Flow**:
    - A new `PrimaryAssetTag` object is instantiated using the `tag_id` and `primary_asset_id` from the `payload`.
    - The new `PrimaryAssetTag` object is added to the database session.
    - The session is committed to persist the changes to the database.
    - The session is refreshed to update the `new_primary_asset_tag` object with any changes made during the commit, such as auto-generated fields.
    - The newly created `PrimaryAssetTag` object is returned.
- **Output**:
    - The function returns the newly created `PrimaryAssetTag` object after it has been added to the database and refreshed.


---
### delete_primary_asset_tag 
The `delete_primary_asset_tag` function removes a specific primary asset tag from the database if it exists and the user is authorized.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to interact with the database.
    - `user`: A `UserToken` object representing the authenticated user making the request.
    - `tag_id`: A UUID representing the unique identifier of the tag to be deleted, provided as a path parameter.
    - `primary_asset_id`: A UUID representing the unique identifier of the primary asset associated with the tag, provided as a path parameter.
- **Control Flow**:
    - The function begins by executing a database query to select a `PrimaryAssetTag` that matches the given `tag_id`, `primary_asset_id`, and the organization ID of the user.
    - If no matching `PrimaryAssetTag` is found, an `HTTPException` with a 404 status code is raised, indicating that the tag was not found or the user is not authorized.
    - If a matching `PrimaryAssetTag` is found, it is deleted from the session.
    - The session is committed to persist the deletion in the database.
    - A `Response` with a 204 status code is returned, indicating successful deletion with no content.
- **Output**:
    - A `Response` object with a 204 status code, indicating successful deletion of the primary asset tag.


