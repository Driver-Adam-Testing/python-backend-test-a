# Purpose
This Python file is a FastAPI router module that defines a set of RESTful API endpoints for managing document sources. The primary functionality provided by this code is the creation, retrieval, and deletion of document sources, which are likely part of a larger document management system. The module imports several components, including permissions, session management, and service classes, to facilitate these operations. The endpoints are protected by permission dependencies, ensuring that only users with the appropriate permissions (either content editor or content readonly) can perform certain actions. The use of UUIDs for document and source identifiers suggests a focus on ensuring unique and secure identification of resources.

The code defines three main API endpoints: a POST endpoint for creating a new document source, a GET endpoint for retrieving an existing document source by its document and source IDs, and a DELETE endpoint for removing a document source. Each endpoint utilizes a `DocumentSourceService` to perform the necessary operations, indicating a separation of concerns where the service layer handles business logic. The endpoints also incorporate session and user token management, which are essential for maintaining user context and security. This module is designed to be part of a larger FastAPI application, providing a focused set of functionalities related to document source management.
# Imports and Dependencies

---
- `uuid`
- `fastapi`
- `app.api.auth`
- `app.api.session`
- `app.schemas.document_source_schema`
- `app.services.document_source_service`


# Global Variables

---
### router 
- **Type**: `APIRouter`
- **Description**: The `router` variable is an instance of FastAPI's `APIRouter` class. It is used to define a group of related API endpoints for managing document sources, including creating, retrieving, and deleting document sources. The `router` is configured with dependencies for permissions, ensuring that only authorized users can perform certain actions.
- **Use**: This variable is used to register and organize API routes related to document source operations, applying necessary permission checks for each route.


# Functions

---
### create_document_source 
The `create_document_source` function creates a new document source using the provided session and document source creation data.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current database session.
    - `user`: An instance of `UserToken` representing the authenticated user making the request.
    - `document_source_create`: An instance of `DocumentSourceCreate` containing the data required to create a new document source.
- **Control Flow**:
    - Instantiate a `DocumentSourceService` object using the provided `session`.
    - Call the `create_document_source` method of the `DocumentSourceService` instance, passing `document_source_create` as an argument.
    - Return the result of the `create_document_source` method call.
- **Output**:
    - The function returns the result of the `create_document_source` method, which is typically the newly created document source object.


---
### delete_document_source 
The `delete_document_source` function deletes a document source identified by document and source IDs using a session and user token.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current database session.
    - `user`: A `UserToken` object representing the authenticated user making the request.
    - `document_id`: A `UUID` representing the unique identifier of the document.
    - `source_id`: A `UUID` representing the unique identifier of the source to be deleted.
- **Control Flow**:
    - Instantiate a `DocumentSourceService` object using the provided session.
    - Call the `delete_document_source` method of the `DocumentSourceService` instance, passing in the `document_id` and `source_id`.
    - Return the result of the `delete_document_source` method call.
- **Output**:
    - The function returns the result of the `delete_document_source` method, which typically indicates the success or failure of the deletion operation.


---
### get_document_source 
The function retrieves a document source by its document and source IDs, raising an exception if not found.
- **Inputs**:
    - `session`: An instance of CurrentSession, representing the current database session.
    - `user`: An instance of UserToken, representing the authenticated user making the request.
    - `document_id`: A UUID representing the unique identifier of the document.
    - `source_id`: A UUID representing the unique identifier of the document source.
- **Control Flow**:
    - Initialize a DocumentSourceService with the provided session.
    - Call the get_document_source method of the service with document_id and source_id.
    - Check if the document source is found; if not, raise an HTTPException with a 404 status code.
    - Return the found document source.
- **Output**:
    - The function returns the document source object if found, otherwise raises an HTTPException with a 404 status code.


