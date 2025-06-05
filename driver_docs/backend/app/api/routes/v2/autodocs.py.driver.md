# Purpose
This Python file defines a FastAPI router that provides an API for managing the generation of "autodocs" for specific pages. The code is structured to handle three main operations: initiating the generation of autodocs, retrieving the current status of an autodoc generation process, and canceling an ongoing autodoc generation. The API endpoints are defined using FastAPI's routing capabilities, with each endpoint handling specific HTTP methods and paths. The `run_autodoc` function initiates the autodoc generation process by validating the input, checking the status of the associated node, and spawning a background task to perform the generation. The `get_autodoc_current_status` function retrieves the latest status of the autodoc generation for a given page, while the `cancel` function allows users to cancel an ongoing generation process.

The code leverages several key components, including SQLAlchemy for database interactions, Pydantic for data validation, and Modal for managing asynchronous tasks. The use of SQLAlchemy's ORM capabilities allows for efficient querying and manipulation of database records related to nodes, versions, and document sources. The code also includes error handling using FastAPI's `HTTPException` to provide meaningful error messages to clients. The file is designed to be part of a larger application, likely serving as a backend service that interacts with a database to manage documentation generation processes. The use of structured data models and clear API definitions suggests that this code is intended to be a robust and scalable solution for managing autodoc generation workflows.
# Imports and Dependencies

---
- `uuid`
- `modal`
- `database.models_v1`
- `database.models_v2`
- `database.models_v2_enums`
- `fastapi`
- `pydantic`
- `sqlalchemy.orm`
- `sqlmodel`
- `app.api.auth`
- `app.api.session`
- `app.core.config`


# Global Variables

---
### router 
- **Type**: `APIRouter`
- **Description**: The `router` variable is an instance of FastAPI's `APIRouter` class. It is used to define a group of related API endpoints for the application, allowing for modular and organized routing.
- **Use**: This variable is used to register and manage API routes for the autodoc generation and status checking functionalities.


# Classes

---
### AutoDocCancelRequest 
- **Type**: `class`
- **Members**:
    - `page_id`: A UUID representing the unique identifier for the page to be canceled.
- **Description**: The `AutoDocCancelRequest` class is a simple data model used to encapsulate the request data for canceling an autodoc generation process. It contains a single attribute, `page_id`, which is a UUID that uniquely identifies the page for which the autodoc generation is to be canceled. This class inherits from `BaseModel`, which is part of the Pydantic library, providing data validation and settings management.
- **Inherits From**:
    - BaseModel


---
### AutoDocCancelResponse 
- **Type**: `class`
- **Members**:
    - `status`: A string indicating the status of the autodoc cancellation response.
- **Description**: The `AutoDocCancelResponse` class is a simple data model that represents the response returned when an autodoc generation process is cancelled. It contains a single attribute, `status`, which is a string that provides information about the cancellation status. This class is used to communicate the result of a cancellation request in the autodoc system.
- **Inherits From**:
    - BaseModel


---
### AutoDocRequest 
- **Type**: `class`
- **Members**:
    - `page_id`: A UUID representing the unique identifier for the page.
    - `config_kind`: An instance of AutoDocConfigKind indicating the configuration type for the autodoc request.
- **Description**: The AutoDocRequest class is a data model used to encapsulate the necessary information for initiating an autodoc generation process. It includes a unique identifier for the page and a configuration kind that specifies the type of autodoc configuration to be applied. This class is utilized in the API endpoint to trigger the autodoc generation process.
- **Inherits From**:
    - BaseModel


---
### AutoDocResponse 
- **Type**: `class`
- **Members**:
    - `status`: An instance of AutoDocStatusHistory representing the status of the autodoc process.
- **Description**: The `AutoDocResponse` class is a simple data model that extends the `BaseModel` from Pydantic. It is designed to encapsulate the status of an autodoc process, represented by an instance of `AutoDocStatusHistory`. This class is likely used to structure the response data for API endpoints related to the autodoc generation process, providing a standardized way to convey the current status of the autodoc operation.
- **Inherits From**:
    - BaseModel


# Functions

---
### cancel 
The `cancel` function stops an ongoing autodoc generation process for a specified page if it is currently generating.
- **Inputs**:
    - `user`: A `UserToken` object representing the authenticated user making the request.
    - `session`: A `CurrentSession` object representing the current database session.
    - `input`: An `AutoDocCancelRequest` object containing the `page_id` of the page for which the autodoc generation is to be cancelled.
- **Control Flow**:
    - Retrieve the `Node` object associated with the given `page_id` and the user's organization from the database.
    - Check if the `Node`'s version status is `GENERATING`; if not, raise an HTTP 400 exception indicating that autodocs is not currently generating.
    - Set the `Node`'s version status to `GENERATION_COMPLETE` to indicate the page has returned to its normal state.
    - Commit the changes to the database to update the version status.
    - Retrieve the most recent `AutoDocStatusHistory` entry for the given `page_id` from the database.
    - If no `AutoDocStatusHistory` entry is found, raise an HTTP 404 exception indicating no autodocs status was found.
    - Retrieve the `call_id` from the `AutoDocStatusHistory` entry and use it to cancel the corresponding `modal.FunctionCall`.
    - Return an `AutoDocCancelResponse` indicating that the autodocs generation has been cancelled.
- **Output**:
    - An `AutoDocCancelResponse` object with a status message indicating that the autodocs generation has been cancelled.


---
### get_autodoc_current_status 
The function retrieves the most recent autodoc status for a given page or returns a default status if none exists.
- **Inputs**:
    - `user`: A UserToken object representing the authenticated user making the request.
    - `session`: A CurrentSession object representing the current database session.
    - `page_id`: A UUID representing the unique identifier of the page for which the autodoc status is being queried.
- **Control Flow**:
    - Execute a database query to select the most recent AutoDocStatusHistory record for the given page_id, ordered by creation date in descending order.
    - Check if the query result is None, indicating no status records exist for the given page_id.
    - If no status record exists, return a new AutoDocStatusHistory object with a status of NOT_STARTED and a message indicating that autodoc generation has not started.
    - If a status record exists, return the most recent AutoDocStatusHistory object retrieved from the database.
- **Output**:
    - Returns an AutoDocStatusHistory object representing the current status of autodoc generation for the specified page.


---
### run_autodoc 
The `run_autodoc` function initiates the generation of an autodoc for a specified page node based on the provided configuration kind, ensuring prerequisites are met and updating the status accordingly.
- **Inputs**:
    - `user`: A `UserToken` object representing the authenticated user, used to verify organization access.
    - `session`: A `CurrentSession` object representing the current database session for executing queries and transactions.
    - `input`: An `AutoDocRequest` object containing the `page_id` of the node to generate the autodoc for and the `config_kind` specifying the type of autodoc configuration.
- **Control Flow**:
    - Retrieve the node associated with the given `page_id` and ensure it belongs to the user's organization.
    - Fetch all document sources related to the specified page node.
    - Raise an HTTP 404 error if no document sources are found for the page.
    - Check if the node's version status is already 'GENERATING' and raise an HTTP 400 error if so.
    - Based on the `config_kind`, perform specific checks on the document sources to ensure they meet the requirements for the autodoc generation.
    - Raise an HTTP 400 error if the `config_kind` is invalid or if the document sources do not meet the required conditions.
    - Look up the `run_autodoc` function in the modal environment specified by the settings.
    - Set the node's version status to 'GENERATING' and add it to the session.
    - Spawn a new autodoc generation task using the `run_autodoc` function with the specified `page_node_id` and `config_kind`.
    - Create a new `AutoDocStatusHistory` entry with the status 'RETRIEVING_SOURCES' and add it to the session.
    - Commit the session to save changes to the database and refresh the `autodoc_status` object.
    - Return the updated `autodoc_status` object.
- **Output**:
    - An `AutoDocStatusHistory` object representing the current status of the autodoc generation process for the specified page node.


