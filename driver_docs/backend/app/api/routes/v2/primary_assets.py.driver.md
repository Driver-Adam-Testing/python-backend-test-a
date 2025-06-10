# Purpose
This Python file is a FastAPI-based module that provides a RESTful API for managing "primary assets" within an application. The code defines several endpoints for CRUD (Create, Read, Update, Delete) operations on primary assets, which are likely entities within a database that represent significant objects or data sets in the application's domain. The endpoints include listing primary assets with optional filtering and sorting, creating new primary assets, updating existing ones, and deleting them. The code leverages SQLAlchemy and SQLModel for database interactions, ensuring that operations are scoped to the user's organization, as indicated by the use of `user.organization_id`.

The file also integrates with AWS S3 for managing related data storage, particularly when deleting primary assets, where it removes associated files from S3 buckets. This involves using the `boto3` library to interact with AWS services, and the code includes error handling for potential issues like non-existent buckets. The module imports various utilities and models from other parts of the application, such as authentication tokens, pagination, and query utilities, indicating that it is part of a larger system. The use of FastAPI's routing and dependency injection features suggests that this file is intended to be part of a web service, providing a structured and secure interface for asset management.
# Imports and Dependencies

---
- `hashlib`
- `getLogger`
- `UUID`
- `boto3`
- `ClientError`
- `InspectorRun`
- `PrimaryAsset`
- `PrimaryAssetTag`
- `Version`
- `Body`
- `HTTPException`
- `Path`
- `Request`
- `selectinload`
- `func`
- `select`
- `UserToken`
- `Pagination`
- `apply_filters_to_query`
- `apply_sorting_to_query`
- `router`
- `ListWithCount`
- `PrimaryAssetCreate`
- `PrimaryAssetDetailRead`
- `PrimaryAssetUpdate`
- `CurrentSession`
- `settings`


# Global Variables

---
### logger
- **Type**: `Logger`
- **Description**: The `logger` variable is an instance of a logger obtained from the Python logging module using the `getLogger` function. It is used to log messages, warnings, and errors throughout the application, providing a way to track and debug the application's behavior.
- **Use**: This variable is used to log warnings and potentially other log levels in the application, particularly in error handling scenarios.


# Functions

---
### create_primary_asset
The `create_primary_asset` function creates a new primary asset in the database using the provided session, user token, and payload data.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to interact with the database.
    - `user`: A `UserToken` object representing the authenticated user, which contains the user's organization ID.
    - `payload`: A `PrimaryAssetCreate` object containing the data required to create a new primary asset, such as display name and kind.
- **Control Flow**:
    - A new `PrimaryAsset` object is instantiated using the display name and kind from the `payload`, and the organization ID from the `user`.
    - The new asset is added to the database session using `session.add(new_asset)`.
    - The session is committed to save the changes to the database with `session.commit()`.
    - The session is refreshed to update the `new_asset` object with any changes made during the commit using `session.refresh(new_asset)`.
    - The newly created `PrimaryAsset` object is returned.
- **Output**:
    - The function returns the newly created `PrimaryAsset` object.


---
### delete_primary_asset
The `delete_primary_asset` function deletes a primary asset from the database and its associated data from AWS S3 storage.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to interact with the database.
    - `user`: A `UserToken` object representing the authenticated user making the request.
    - `primary_asset_id`: A `UUID` representing the unique identifier of the primary asset to be deleted.
- **Control Flow**:
    - The function queries the database to find the primary asset with the given `primary_asset_id` and checks if it belongs to the user's organization.
    - If the asset is not found, an HTTP 404 exception is raised.
    - The function retrieves all `InspectorRun` IDs associated with the asset's versions.
    - It calculates a hash of the user's organization ID to determine the S3 bucket name and constructs a prefix for the asset's data.
    - An S3 resource is initialized using AWS credentials from the settings.
    - The function attempts to delete all objects in the S3 bucket with the specified prefix, handling any `ClientError` exceptions that occur if the bucket does not exist.
    - For each `InspectorRun` ID, the function deletes associated objects from the inspector bucket in S3.
    - The asset is deleted from the database, and the session is committed to save changes.
- **Output**:
    - The function returns the deleted `PrimaryAsset` object.


---
### list_primary_assets
The `list_primary_assets` function retrieves a paginated and optionally filtered list of primary assets for a user's organization, including their most recent version details.
- **Inputs**:
    - `request`: An instance of `Request` containing query parameters for filtering the primary assets.
    - `session`: An instance of `CurrentSession` used to execute database queries.
    - `user`: An instance of `UserToken` representing the authenticated user, used to filter assets by organization.
    - `pagination`: An instance of `Pagination` containing pagination and sorting information.
    - `tag_ids`: An optional string of comma-separated tag IDs to filter primary assets by associated tags.
- **Control Flow**:
    - A SQLAlchemy query is constructed to select `PrimaryAsset` records, preloading related `most_recent_version`, `root_node`, and `creator` entities, and filtering by the user's organization ID.
    - Query parameters from the request are converted to a dictionary and applied as filters to the query using `apply_filters_to_query`.
    - If `tag_ids` is provided, the query is further filtered to include only assets associated with the specified tags using a subquery with `PrimaryAssetTag`.
    - A count query is executed to determine the total number of filtered primary assets.
    - If the pagination sort field is `most_recent_version.root_node.total_files`, the assets are retrieved, sorted in Python by the total files in the root node, and sliced according to pagination limits.
    - Otherwise, the query is sorted using `apply_sorting_to_query` and executed to retrieve the paginated results.
    - The function returns a `ListWithCount` object containing the list of primary assets and the total count.
- **Output**:
    - A `ListWithCount` object containing the list of primary assets and the total count of assets matching the query.


---
### update_primary_asset
The `update_primary_asset` function updates the details of a primary asset in the database based on the provided payload and user context.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to interact with the database.
    - `user`: A `UserToken` object representing the authenticated user making the request.
    - `primary_asset_id`: A `UUID` representing the unique identifier of the primary asset to be updated.
    - `payload`: A `PrimaryAssetUpdate` object containing the new values for the primary asset's fields to be updated.
- **Control Flow**:
    - The function begins by querying the database to find the primary asset with the given `primary_asset_id` that belongs to the organization of the authenticated user.
    - If no such asset is found, an `HTTPException` with a 404 status code is raised, indicating that the primary asset was not found.
    - If the `display_name` in the payload is not `None`, the asset's `display_name` is updated with the new value from the payload.
    - If the `codebase_settings_auto_commit_docs` in the payload is not `None`, the asset's `codebase_settings_auto_commit_docs` is updated with the new value from the payload.
    - The updated asset is added to the session, and the session is committed to save the changes to the database.
    - The session is refreshed to ensure the asset object is updated with the latest data from the database.
    - The updated primary asset is returned.
- **Output**:
    - The function returns the updated `PrimaryAsset` object after applying the changes from the payload.


