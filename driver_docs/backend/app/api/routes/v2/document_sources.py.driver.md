# Purpose
This Python file is a FastAPI-based module that defines a set of RESTful API endpoints for managing `DocumentSource` entities within a database. The code provides CRUD (Create, Read, Update, Delete) operations specifically tailored for handling document sources, which are likely part of a larger application dealing with document management or content organization. The endpoints include functionalities to list document sources with pagination and filtering, create single or batch document sources, and delete single or batch document sources. The operations are secured by user authentication, ensuring that actions are performed within the context of a user's organization.

The file imports several components from external libraries and internal modules, such as SQLAlchemy for database interactions, FastAPI for defining the API routes, and custom utility functions for query manipulation. The endpoints are defined using FastAPI's routing capabilities, with each function decorated to specify the HTTP method and path. The code leverages SQLAlchemy's ORM features to construct and execute database queries, ensuring efficient data retrieval and manipulation. The use of models and schemas indicates a structured approach to data handling, with clear definitions for input and output data formats. This module is designed to be part of a larger application, providing a focused set of functionalities related to document source management.
# Imports and Dependencies

---
- `uuid`
- `database.models_v1`
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
### batch_create_document_sources 
The `batch_create_document_sources` function creates multiple document sources by first deleting any existing sources with the same page_node_id and then adding new ones to the database session.
- **Inputs**:
    - `session`: An instance of CurrentSession used to interact with the database.
    - `user`: A UserToken object representing the authenticated user making the request.
    - `payload`: A list of DocumentSourceCreate objects containing the data for the document sources to be created.
- **Control Flow**:
    - Initialize an empty list `created_document_sources` to store the newly created document sources.
    - Iterate over each `data` item in the `payload` list.
    - For each `data`, execute a delete operation on the `DocumentSource` table to remove any existing entries with the same `page_node_id`.
    - Create a list of new `DocumentSource` instances using the data from the `payload`.
    - Add all new document sources to the session using `session.add_all()`.
    - Commit the session to save the changes to the database.
    - Refresh each new document source in the session to ensure it has the latest data from the database.
    - Append each refreshed document source to the `created_document_sources` list.
    - Return the `created_document_sources` list.
- **Output**:
    - A list of DocumentSourceDetailRead objects representing the newly created document sources.


---
### batch_delete_document_sources 
The function `batch_delete_document_sources` deletes multiple document sources based on a list of criteria and returns the success status of each deletion.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to interact with the database.
    - `user`: A `UserToken` object representing the authenticated user, used to verify organization access.
    - `payload`: A list of `DocumentSourceCreate` objects containing the source_node_id and page_node_id for each document source to be deleted.
- **Control Flow**:
    - Initialize an empty list `deletion_results` to store the result of each deletion operation.
    - Iterate over each `data` item in the `payload` list.
    - For each `data`, execute a SQL delete operation on the `DocumentSource` table where the `source_node_id` and `page_node_id` match those in `data`, and the `organization_id` matches that of the `user`.
    - Commit the transaction to the database.
    - Append `True` to `deletion_results` if a row was deleted (i.e., `result.rowcount > 0`), otherwise append `False`.
    - Return the `deletion_results` list containing the success status of each deletion.
- **Output**:
    - A list of boolean values indicating the success (True) or failure (False) of each document source deletion.


---
### create_document_source 
The `create_document_source` function creates a new `DocumentSource` record in the database and returns the created record.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to interact with the database.
    - `user`: An instance of `UserToken` representing the authenticated user making the request.
    - `payload`: An instance of `DocumentSourceCreate` containing the data required to create a new `DocumentSource`, specifically `source_node_id` and `page_node_id`.
- **Control Flow**:
    - A new `DocumentSource` instance is created using the `source_node_id` and `page_node_id` from the `payload`.
    - The new `DocumentSource` instance is added to the database session.
    - The session is committed to save the new `DocumentSource` to the database.
    - The session is refreshed to ensure the `new_document_source` instance is updated with any changes made during the commit, such as auto-generated fields.
    - The function returns the `new_document_source` instance.
- **Output**:
    - The function returns a `DocumentSourceDetailRead` object representing the newly created `DocumentSource`.


---
### delete_document_source 
The `delete_document_source` function deletes a document source from the database based on specified node IDs and returns a boolean indicating success.
- **Inputs**:
    - `session`: An instance of CurrentSession used to interact with the database.
    - `user`: A UserToken object representing the authenticated user, used to verify organization access.
    - `page_node_id`: A UUID representing the ID of the page node associated with the document source to be deleted.
    - `source_node_id`: A UUID representing the ID of the source node associated with the document source to be deleted.
- **Control Flow**:
    - Execute a SQL delete operation on the DocumentSource table where the source_node_id and page_node_id match the provided arguments and the organization_id matches the user's organization_id.
    - Commit the transaction to the database to finalize the deletion.
    - Return True if the delete operation affected any rows, indicating a successful deletion, otherwise return False.
- **Output**:
    - A boolean value indicating whether the document source was successfully deleted (True) or not (False).


---
### list_document_sources 
The `list_document_sources` function retrieves a list of document sources from the database, applying filters and sorting based on the request parameters, and returns the results along with the total count.
- **Inputs**:
    - `request`: An instance of `Request` containing query parameters for filtering the document sources.
    - `session`: An instance of `CurrentSession` used to execute database queries.
    - `user`: An instance of `UserToken` representing the authenticated user, used to filter document sources by organization.
    - `pagination`: An instance of `Pagination` containing sorting and pagination information for the query.
- **Control Flow**:
    - Check if the `pagination.sort_by` is set to 'updated_at' and set it to `None` if true.
    - Construct a SQL query to select `DocumentSource` records, joining related tables for efficient data retrieval.
    - Apply eager loading strategies using `selectinload` to optimize database access for related entities.
    - Filter the query to only include document sources belonging to the user's organization using `PrimaryAsset.organization_id`.
    - Convert the request's query parameters into a dictionary and apply them as filters to the query using `apply_filters_to_query`.
    - Create a count query to determine the total number of document sources matching the filters and execute it to get the count.
    - Apply sorting to the query based on the `pagination` object using `apply_sorting_to_query`.
    - Execute the final query to retrieve the list of document sources.
    - Return the list of document sources along with the total count in a `ListWithCount` object.
- **Output**:
    - A `ListWithCount` object containing the list of `DocumentSourceRead` objects and the total count of document sources matching the query.


