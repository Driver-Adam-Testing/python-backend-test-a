# Purpose
This Python file is a FastAPI router module that defines a set of RESTful API endpoints for managing and interacting with content within an application. The primary purpose of this module is to provide a structured interface for performing CRUD (Create, Read, Update, Delete) operations on content entities, as well as additional functionalities like exporting content and retrieving associated metadata such as tags and document sources. The endpoints are organized to handle various HTTP methods, including GET, PUT, DELETE, and POST, each serving a specific function such as listing content, retrieving content by ID, updating content, deleting content, and exporting content to a different format.

The module leverages FastAPI's routing capabilities and dependency injection to enforce permissions and manage user sessions. It imports several components from other parts of the application, such as `ContentService` for business logic, and various schemas for request and response validation. The endpoints are protected by permissions like `ContentReadonlyPermission` and `ContentEditorPermission`, ensuring that only authorized users can perform certain actions. The use of UUIDs for content identification and the integration with external services like S3 for content downloads highlight the module's design for scalability and integration with broader application infrastructure. Overall, this module serves as a critical component in the application's backend, facilitating content management and interaction through a well-defined API.
# Imports and Dependencies

---
- `typing`
- `uuid`
- `database.models_v1`
- `fastapi`
- `fastapi.responses`
- `app.api.auth`
- `app.api.session`
- `app.schemas.content_schema`
- `app.services.content_service`


# Global Variables

---
### router 
- **Type**: `APIRouter`
- **Description**: The `router` variable is an instance of FastAPI's `APIRouter` class. It is used to define a group of related API endpoints that can be included in the main application. This allows for modular and organized routing in a FastAPI application.
- **Use**: The `router` is used to register various HTTP endpoints for content management operations, such as listing, retrieving, updating, and deleting content.


# Functions

---
### delete_content 
The `delete_content` function removes a content item from the database using the provided session, user, and content ID.
- **Inputs**:
    - `session`: An instance of CurrentSession representing the current database session.
    - `user`: An instance of UserToken representing the current user, which includes the user's organization ID.
    - `content_id`: A UUID representing the unique identifier of the content to be deleted.
- **Control Flow**:
    - Initialize a ContentService object using the provided session.
    - Call the `delete_content` method of the ContentService object, passing the user's organization ID and the content ID to delete the specified content.
- **Output**:
    - The function returns None, indicating that it performs its operation without returning any value.


---
### export_markdown_content_to_rst 
The function `export_markdown_content_to_rst` converts Markdown content to reStructuredText (RST) format and returns it as a downloadable file.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current session context.
    - `request`: An instance of `ExportSingleRequest` containing the Markdown content to be converted.
- **Control Flow**:
    - Initialize a `ContentService` object using the provided session.
    - Convert the Markdown content from the request to RST format using the `convert_markdown_to_rst` method of `ContentService`.
    - Create and return a `StreamingResponse` with the converted RST content, setting the media type to 'text/x-rst' and specifying a content-disposition header for file download.
- **Output**:
    - A `StreamingResponse` object containing the converted RST content, ready for download as a file.


---
### get_content_by_id 
The `get_content_by_id` function retrieves content details by its unique identifier (UUID) for a specific user session.
- **Inputs**:
    - `session`: A `CurrentSession` object representing the current user session.
    - `user`: A `UserToken` object representing the current user, which includes the user's organization ID.
    - `content_id`: A `UUID` object representing the unique identifier of the content to be retrieved.
- **Control Flow**:
    - A `ContentService` object is instantiated using the provided `session`.
    - The `get_content_by_id` method of the `ContentService` object is called with `content_id` and `user.organization_id` as arguments.
    - The result of the `get_content_by_id` method call is returned.
- **Output**:
    - The function returns a `DerivedContent` object containing the details of the content identified by the given UUID.


---
### get_content_root_by_id 
The function retrieves the root codebase content record for a specified content ID.
- **Inputs**:
    - `session`: The current session object, representing the active database session.
    - `user`: The current user object, containing user authentication and organization information.
    - `content_id`: The UUID of the content for which the root codebase content record is to be retrieved.
- **Control Flow**:
    - A ContentService object is instantiated using the provided session.
    - The get_content_root_by_id method of the ContentService object is called with the content_id and the user's organization_id as arguments.
    - The result of the method call, which is the root codebase content details, is returned.
- **Output**:
    - The function returns a DerivedContent object containing the root codebase content details for the specified content ID.


---
### get_content_tags 
The `get_content_tags` function retrieves tags associated with a specific content item using a content service.
- **Inputs**:
    - `session`: The current session object, representing the active session context.
    - `user`: The current user object, containing user-specific information such as organization ID.
    - `content_id`: The UUID of the content for which tags are to be retrieved.
- **Control Flow**:
    - Initialize a `ContentService` object using the provided `session`.
    - Call the `get_content_tags` method of the `ContentService` object, passing `content_id` and `user.organization_id` as arguments.
    - Return the result of the `get_content_tags` method call.
- **Output**:
    - A `ContentTagsResponse` object containing the list of tags associated with the specified content.


---
### get_document_sources 
The function `get_document_sources` retrieves the sources associated with a specific document identified by its content ID.
- **Inputs**:
    - `session`: The current session object, which represents the active session for the request.
    - `user`: The current user object, which contains information about the user making the request, including their organization ID.
    - `content_id`: The UUID of the content for which the document sources are being requested.
- **Control Flow**:
    - A `ContentService` object is instantiated using the provided `session`.
    - The `get_content_sources` method of the `ContentService` object is called with `content_id` and `user.organization_id` as arguments.
    - The result of the `get_content_sources` method call is returned as the output of the function.
- **Output**:
    - The function returns a `ContentSourceResponse` object, which contains details about the document sources associated with the specified content ID.


---
### get_download_content_by_id 
The function retrieves a download URL from S3 for a given node ID using the current session and user information.
- **Inputs**:
    - `session`: The current session object, representing the active session context.
    - `user`: The current user object, containing user-specific information such as organization ID.
    - `node_id`: The UUID of the node for which the download URL is requested.
- **Control Flow**:
    - A ContentService object is instantiated using the provided session.
    - The get_content_download_url method of the ContentService object is called with the node_id and the user's organization_id as arguments.
    - The result of the get_content_download_url method call is returned.
- **Output**:
    - A DownloadContentResponse object containing the download URL and related content details.


---
### list_content 
The `list_content` function retrieves a list of content items based on various filter criteria and returns the results.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current session context.
    - `user`: An instance of `UserToken` representing the current user, including their organization ID.
    - `latest_version_only`: A boolean flag indicating whether to retrieve only the latest version of the content (default is `False`).
    - `limit`: An optional integer specifying the maximum number of content items to return (default is `20`).
    - `offset`: An optional integer specifying the number of content items to skip before starting to collect the result set (default is `0`).
    - `content_type_name`: An optional list of strings specifying the content type names to filter by.
    - `order`: An optional integer specifying the order of the content items.
    - `sort_by`: An optional string specifying the field by which to sort the content items.
    - `sort_direction`: An optional string specifying the direction of sorting, either 'ASC' or 'DESC' (default is 'ASC').
    - `status`: An optional string specifying the status of the content to filter by.
    - `tag`: An optional list of strings specifying tags to filter the content by.
    - `tag_id`: An optional list of strings specifying tag IDs to filter the content by.
    - `text`: An optional string specifying text to search for within the content.
    - `version_id`: An optional list of strings specifying version IDs to filter the content by.
- **Control Flow**:
    - Initialize a `ContentService` instance using the provided `session`.
    - Call the `get_list_content` method of the `ContentService` instance, passing the user's organization ID and a `ListContentInput` object constructed with the provided filter criteria.
    - Return the results obtained from the `get_list_content` method.
- **Output**:
    - The function returns an instance of `ListContentResults`, which contains the list of content items matching the provided filter criteria.


---
### update_content 
The `update_content` function updates a content record in the database using the provided update data.
- **Inputs**:
    - `session`: An instance of CurrentSession representing the current database session.
    - `user`: An instance of UserToken representing the current user, which includes the user's organization ID.
    - `content_id`: A UUID representing the unique identifier of the content to be updated.
    - `update_data`: A dictionary containing the data to update the content with.
- **Control Flow**:
    - Instantiate a ContentService object using the provided session.
    - Call the `edit_content` method of the ContentService object, passing the user's organization ID, the content ID, and the update data.
    - Return the result of the `edit_content` method call.
- **Output**:
    - The function returns an instance of DerivedContent, which represents the updated content record.


