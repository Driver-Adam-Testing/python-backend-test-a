# Purpose
This Python file is a FastAPI-based module that provides API endpoints for managing content pages and templates within an application. The code defines three main endpoints: `edit_page_CONVENIENCE_METHOD`, `new_page`, and `new_template`. These endpoints facilitate the creation and modification of content associated with user organizations. The `edit_page_CONVENIENCE_METHOD` endpoint allows users to update existing derived content, ensuring that the content belongs to the user's organization and updating the content's name if provided. The `new_page` and `new_template` endpoints enable the creation of new pages and templates, respectively, by generating unique names based on existing assets and establishing the necessary database relationships for these new entities.

The code leverages SQLModel for database interactions, using models such as `DerivedContent`, `PrimaryAsset`, `Version`, and `Node` to represent different components of the content management system. It also uses FastAPI's dependency injection to handle user authentication and session management, ensuring that operations are performed within the context of the current user and session. The endpoints return appropriate HTTP responses, with the `new_page` and `new_template` endpoints providing detailed content information in the response model. This module is designed to be part of a larger application, focusing on content management functionalities and integrating with other components through shared models and session handling.
# Imports and Dependencies

---
- `uuid`
- `database.models_v1`
- `database.models_v2`
- `database.models_v2_enums`
- `fastapi`
- `sqlmodel`
- `app.api.auth`
- `app.api.routes.v2.router`
- `app.api.routes.v2.schemas`
- `app.api.session`


# Functions

---
### edit_page_CONVENIENCE_METHOD 
The `edit_page_CONVENIENCE_METHOD` function updates the content and content name of a derived content entity if it belongs to the user's organization and commits the changes to the database.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to interact with the database.
    - `user`: A `UserToken` object representing the authenticated user making the request.
    - `node_id`: A `UUID` representing the unique identifier of the node to be edited, provided as a path parameter.
    - `payload`: A `DerivedContentUpdate` object containing the new content and/or content name to update, provided in the request body.
- **Control Flow**:
    - The function begins by querying the database to fetch the `DerivedContent` associated with the given `node_id` and checks if it belongs to the user's organization.
    - If no such derived content is found, an `HTTPException` with a 404 status code is raised, indicating the content is not found or the user is not authorized.
    - If the `payload` contains a new content value, it updates the `content` field of the derived content.
    - If the `payload` contains a new content name, it updates the `content_name` field of the derived content and attempts to update the `display_name` of the associated `PrimaryAsset` if it is of kind `PAGE` or `PAGE_TEMPLATE`.
    - The function adds the updated derived content (and possibly the primary asset) to the session, commits the transaction, and refreshes the derived content to reflect the changes.
    - Finally, it returns a `Response` with a status code of 202, indicating the request has been accepted for processing.
- **Output**:
    - A `Response` object with a status code of 202, indicating the request has been accepted for processing.


---
### new_page 
The `new_page` function creates a new page asset with a unique name for a user's organization and returns its details.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to interact with the database.
    - `user`: An instance of `UserToken` representing the authenticated user, containing user and organization information.
- **Control Flow**:
    - Query the database for existing `PrimaryAsset` entries with names like 'Untitled Page X' for the user's organization.
    - Iterate over the existing assets to find the highest number used in the 'Untitled Page X' naming pattern.
    - Create a new `PrimaryAsset` with a name incremented from the highest number found.
    - Add and commit the new `PrimaryAsset` to the database.
    - Check if the user exists in the `UserCache`; if not, create and commit a new entry for the user.
    - Create a new `Version` associated with the new `PrimaryAsset`, add and commit it to the database.
    - Create a `VersionCreator` entry linking the user to the new version, add and commit it to the database.
    - Create a `Node` associated with the new version, add and commit it to the database.
    - Create a `DerivedContent` entry linked to the new node, add and commit it to the database.
    - Refresh the `DerivedContent` to ensure the node relationship is populated.
    - Return the validated `ContentDetailRead` model of the new `DerivedContent`.
- **Output**:
    - A `ContentDetailRead` object representing the newly created page asset.


---
### new_template 
The `new_template` function creates a new template asset with a unique name for a user's organization and returns its details.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to interact with the database.
    - `user`: An instance of `UserToken` representing the authenticated user, containing information like organization ID.
- **Control Flow**:
    - Query the database for existing template assets with names starting with 'Untitled Template' for the user's organization.
    - Iterate over the existing assets to extract and find the maximum number used in the template names.
    - Create a new `PrimaryAsset` with a display name incremented by one from the maximum number found.
    - Add and commit the new `PrimaryAsset` to the session.
    - Create a new `Version` associated with the new `PrimaryAsset`, set its status to `GENERATION_COMPLETE`, and commit it to the session.
    - Create a new `Node` associated with the new `Version`, set its relative path to 'template', and commit it to the session.
    - Create a new `DerivedContent` associated with the new `Node`, set its content kind to 'template', and commit it to the session.
    - Refresh the session to ensure the new `DerivedContent` is up-to-date.
    - Return the validated model of the new `DerivedContent`.
- **Output**:
    - A `ContentDetailRead` object representing the newly created template asset.


