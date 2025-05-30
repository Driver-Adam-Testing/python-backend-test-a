# Purpose
This Python file is designed to interact with a database using asynchronous operations, primarily focusing on managing and retrieving version and node data. It provides a set of functions that facilitate operations such as fetching a version by its ID, attempting to retrieve a previous version, creating an inspector run, and obtaining the latest run associated with a version ID. Additionally, it includes functionality to retrieve analyzable nodes by version ID and to get derived content for a specific node. The code leverages SQLModel for ORM capabilities and uses asynchronous sessions to interact with the database, ensuring efficient and non-blocking database operations.

The file is structured as a collection of functions that serve as a backend utility for managing version control and inspection runs within a database context. It imports various models and enums from a database module, indicating its role in a larger application that likely involves version management and content inspection. The functions are designed to be used in an asynchronous environment, suggesting that they are part of a larger asynchronous application or service. The presence of a synchronous function, `get_usage_balance_in_bytes`, indicates that the file also includes functionality for calculating usage metrics, specifically converting usage balance from SLOC to bytes. Overall, this file acts as a backend utility for database operations related to versioning and content analysis.
# Imports and Dependencies

---
- `uuid`
- `database.models_v1.DerivedContent`
- `database.models_v1.InspectorRun`
- `database.models_v2.Node`
- `database.models_v2.Version`
- `database.models_v2_enums.ContentKind`
- `database.models_v2_enums.NodeKind`
- `database.models_v2_enums.VersionStatus`
- `sqlmodel.ext.asyncio.session.AsyncSession`
- `database.db.async_engine`
- `sqlalchemy.orm.selectinload`
- `sqlmodel.select`
- `modal`
- `database.db.engine`
- `shared.interfaces.usage.usage_schema.UsageMetricUnitType`
- `shared.usage.usage_service.UsageService`
- `sqlmodel.Session`


# Functions

---
### create_inspector_run 
The function `create_inspector_run` creates a new `InspectorRun` record in the database and returns its unique identifier.
- **Inputs**:
    - `version_id`: A UUID representing the version ID for which the inspector run is being created.
- **Control Flow**:
    - Import necessary modules and functions, including `modal` and `async_engine`.
    - Retrieve the current function call ID using `modal.current_function_call_id()`.
    - Open an asynchronous session with the database using `AsyncSession` and `async_engine`.
    - Create a new `InspectorRun` object with the provided `version_id`, the retrieved `modal_call_id`, and a `None` value for `inspection_version_id`.
    - Add the `InspectorRun` object to the session and commit the transaction to save it to the database.
    - Refresh the session to update the `InspectorRun` object with the database-generated ID.
    - Retrieve the `id` of the newly created `InspectorRun` object and store it in `run_id`.
    - Return the `run_id` as the function's output.
- **Output**:
    - The function returns a UUID representing the ID of the newly created `InspectorRun` record.


---
### get_analyzable_nodes_by_version_id 
The function retrieves a list of analyzable nodes for a given version ID and set of content types from the database.
- **Inputs**:
    - `version_id`: A UUID representing the version ID to filter nodes by.
    - `content_types`: A set of NodeKind values representing the types of nodes to include in the results.
- **Control Flow**:
    - Import necessary modules and classes for database interaction and query execution.
    - Establish an asynchronous session with the database using AsyncSession and async_engine.
    - Construct a SQL query to select nodes from the Node table where the version_id matches the provided version_id and the node kind is within the specified content_types.
    - Execute the query asynchronously and retrieve the results.
    - Iterate over the results to check each node's kind.
    - Determine if a node is a directory or an analyzable file by checking its kind and metadata.
    - Append nodes that are directories or analyzable files to the result list.
    - Return the list of analyzable nodes.
- **Output**:
    - A list of Node objects that are either directories or analyzable files, filtered by the specified version ID and content types.


---
### get_source_code_derived_content 
The function retrieves a DerivedContent object from the database based on a given node ID and content kind.
- **Inputs**:
    - `node_id`: A UUID representing the unique identifier of the node for which the derived content is to be retrieved.
- **Control Flow**:
    - Import necessary modules and classes, including async_engine from the database and select from sqlmodel.
    - Create an asynchronous session with the database using AsyncSession and async_engine.
    - Construct a SQL statement to select a DerivedContent object where the node_id matches the provided node_id and the content_kind is CODEBASE_FILE.
    - Execute the SQL statement asynchronously and retrieve the first matching result using session.exec(statement).one().
    - Return the retrieved DerivedContent object.
- **Output**:
    - The function returns a DerivedContent object that matches the specified node_id and content_kind criteria.


---
### get_usage_balance_in_bytes 
The function `get_usage_balance_in_bytes` retrieves and converts the usage balance for a given organization from SLOC to bytes.
- **Inputs**:
    - `org_id`: A string representing the organization ID for which the usage balance is to be retrieved.
- **Control Flow**:
    - Import necessary modules and classes including `engine`, `UsageMetricUnitType`, `UsageService`, and `Session`.
    - Establish a session with the database using `Session(engine)`.
    - Create an instance of `UsageService` with the current session.
    - Call `get_usage_balance` on the `UsageService` instance with `org_id` to retrieve the usage balance in SLOC.
    - Convert the retrieved usage balance from SLOC to bytes using `convert_to(UsageMetricUnitType.BYTES)`.
    - Return the converted usage balance in bytes.
- **Output**:
    - An integer representing the usage balance in bytes for the specified organization.


---
### get_version_by_id 
The function retrieves a specific version from the database using its unique identifier.
- **Inputs**:
    - `version_id`: A UUID representing the unique identifier of the version to be retrieved.
- **Control Flow**:
    - Import necessary modules and classes for database interaction and query construction.
    - Establish an asynchronous session with the database using AsyncSession and the async_engine.
    - Construct a SQL query using the select function to retrieve a Version object where the Version.id matches the provided version_id.
    - Use selectinload to eagerly load related objects, specifically the primary_asset and root_node of the Version.
    - Execute the query asynchronously and retrieve the single result using the one() method.
    - Return the retrieved Version object.
- **Output**:
    - The function returns a Version object corresponding to the provided version_id, including its primary_asset and root_node loaded eagerly.


---
### try_get_latest_run_from_version_id 
The function attempts to retrieve the latest run ID associated with a given version ID from the database.
- **Inputs**:
    - `version_id`: A UUID representing the version ID for which the latest run ID is to be retrieved.
- **Control Flow**:
    - Import necessary modules and classes, including the async database engine and SQLModel's select function.
    - Create an asynchronous session with the database using AsyncSession and the async_engine.
    - Construct a SQL statement to select from the InspectorRun table where the version_id matches the provided version_id, ordering the results by the created_at field in descending order to get the latest run first.
    - Execute the SQL statement asynchronously and retrieve the first result from the query.
    - Check if the result is None, indicating no runs are associated with the given version ID, and return None in this case.
    - If a result is found, return the ID of the latest InspectorRun.
- **Output**:
    - The function returns the UUID of the latest InspectorRun associated with the given version ID, or None if no such run exists.


---
### try_get_prev_version 
The function `try_get_prev_version` attempts to retrieve the previous version of a given version if it exists and meets certain criteria.
- **Inputs**:
    - `version_id`: A UUID representing the unique identifier of the version for which the previous version is being queried.
- **Control Flow**:
    - Import necessary modules and classes for database operations and query building.
    - Create an asynchronous session with the database using `AsyncSession`.
    - Construct a SQL query to select the `Version` object with the given `version_id`.
    - Execute the query to retrieve the current version object.
    - Construct another SQL query to select the previous version of the retrieved version, ensuring it has a status of `GENERATION_COMPLETE` and preloading its primary asset.
    - Execute the query to retrieve the previous version object, if it exists.
    - Return the previous version object or `None` if no such version exists.
- **Output**:
    - The function returns a `Version` object representing the previous version if it exists and meets the criteria, otherwise it returns `None`.


