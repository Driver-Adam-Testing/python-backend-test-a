# Purpose
This Python code defines a class `DataScope` using the Pydantic library, which is designed to manage and represent the scope of an agent's operation within a database context. The primary functionality of this class is to handle a collection of nodes, represented by the `DataScopeNode` inner class, which are lazy-loaded from a database. The `DataScope` class provides methods to retrieve nodes by their identifiers, create child data scopes based on specific identifiers, and generate a human-readable summary of the nodes it contains. The class interacts with a database using SQLAlchemy and SQLModel to execute queries and load related data, such as versions and primary assets, ensuring that the nodes are correctly associated with their respective organization IDs.

The `DataScope` class is a specialized component that provides a focused functionality for managing access to nodes within a database, making it suitable for use in applications that require controlled access to data based on user and organization contexts. It is not a standalone script but rather a part of a larger system, likely intended to be imported and used within other modules or services. The class defines a clear API for interacting with the nodes, including methods for retrieving nodes, creating sub-scopes, and summarizing the data scope, making it a crucial part of a data management or access control system.
# Imports and Dependencies

---
- `uuid`
- `database.db`
- `database.models_v2`
- `pydantic`
- `sqlalchemy.orm`
- `sqlmodel`


# Global Variables

---
### _cached_nodes 
- **Type**: `list[DataScope.DataScopeNode] | None`
- **Description**: The `_cached_nodes` variable is a private attribute of the `DataScope` class, intended to store a list of `DataScopeNode` objects. It is initially set to `None` and is used to cache the nodes that are loaded from the database, preventing redundant database queries.
- **Use**: This variable is used to store and cache the nodes associated with a `DataScope` instance, optimizing access by avoiding repeated database queries.


# Classes

---
### DataScope 
- **Type**: `class`
- **Members**:
    - `node_ids`: A list of UUIDs representing the node IDs within the data scope.
    - `user_id`: A string representing the user ID associated with the data scope.
    - `organization_id`: A string representing the organization ID associated with the data scope.
    - `_cached_nodes`: A cached list of DataScopeNode objects, initially set to None.
- **Description**: The `DataScope` class, inheriting from `BaseModel`, defines the operational scope of an agent by managing access to a collection of nodes within a specified organization. It includes a nested `DataScopeNode` class that represents individual nodes, which are lazy-loaded from a database. The class provides methods to retrieve nodes by identifier, create child data scopes based on node identifiers, and generate a human-readable summary of the nodes grouped by their primary asset display names. The `DataScope` class is designed to handle node access efficiently by caching nodes and ensuring that identifiers are valid within the current scope.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### DataScope.get_node_by_identifier
The function `get_node_by_identifier` retrieves a `DataScopeNode` from a list of nodes based on a given identifier string.
- **Inputs**:
    - `identifier`: A string representing the identifier of the node, formatted as '{version_display_name}/{relative_path}'.
- **Control Flow**:
    - Iterates over each `DataScopeNode` in the `nodes` list.
    - For each node, calls the `get_identifier` method to obtain its identifier.
    - Compares the obtained identifier with the input `identifier`.
    - If a match is found, returns the corresponding `DataScopeNode`.
    - If no match is found after checking all nodes, returns `None`.
- **Output**:
    - Returns a `DataScopeNode` object if a node with the matching identifier is found, otherwise returns `None`.


---
#### DataScope.nodes
The `nodes` function retrieves and caches a list of `DataScopeNode` objects corresponding to the node IDs stored in the `DataScope` instance.
- **Inputs**:
    - None
- **Control Flow**:
    - Check if `_cached_nodes` is `None` to determine if nodes need to be loaded from the database.
    - If `_cached_nodes` is `None`, open a database session using `get_session()`.
    - Construct a SQL query to select `Node` objects where the `Node.id` is in `self.node_ids`, including related `Version` and `PrimaryAsset` data using `selectinload`.
    - Execute the query and retrieve all matching nodes.
    - Convert each retrieved `Node` object into a `DataScopeNode` and store them in `_cached_nodes`.
    - Return the list of `DataScopeNode` objects from `_cached_nodes`.
- **Output**:
    - A list of `DataScopeNode` objects corresponding to the node IDs in the `DataScope` instance.


---
#### DataScope.to_child_datascope
The `to_child_datascope` function creates a new `DataScope` containing nodes that match given identifiers, ensuring they are children of the current datascope.
- **Inputs**:
    - `identifiers`: A list of string identifiers, each in the format '{version_display_name}/{relative_path}', representing nodes to be included in the new DataScope.
- **Control Flow**:
    - Collect existing node identifiers from the current DataScope.
    - For each identifier in the input list, check if it starts with any existing node identifier; raise a ValueError if not.
    - Attempt to match each identifier to a node in the current DataScope and collect their node IDs.
    - If not all identifiers match existing nodes, query the database to find nodes matching the identifiers based on their version display name and relative path.
    - Create a new DataScope with the matched node IDs, user ID, and organization ID.
    - If all identifiers matched existing nodes, cache the nodes in the new DataScope and return it.
- **Output**:
    - A new `DataScope` object containing node IDs that match the given identifiers, along with the user ID and organization ID.


---
#### DataScope.to_human_readable_summary
The `to_human_readable_summary` function generates a human-readable summary of nodes grouped by their primary asset display names.
- **Inputs**:
    - None
- **Control Flow**:
    - Initialize an empty dictionary `grouped_identifiers` to store identifiers grouped by primary asset display names.
    - Iterate over each node in `self.nodes`.
    - For each node, retrieve the primary asset display name and construct an identifier using the version display name and relative path.
    - Check if the primary asset display name is already a key in `grouped_identifiers`; if not, initialize it with an empty list.
    - Append the constructed identifier to the list corresponding to the primary asset display name in `grouped_identifiers`.
    - Initialize an empty list `summary_lines` to store the formatted summary lines.
    - Iterate over each primary asset and its identifiers in `grouped_identifiers`.
    - For each primary asset, append a line to `summary_lines` indicating the asset's paths.
    - For each identifier under a primary asset, append a formatted line to `summary_lines`.
    - Join all lines in `summary_lines` with newline characters and return the resulting string.
- **Output**:
    - A string that contains a human-readable summary of nodes, grouped by their primary asset display names, with each identifier listed under its respective asset.


**Nested Classes**
    - DataScopeNode


---
### DataScopeNode 
- **Type**: `class`
- **Members**:
    - `_node`: Stores the Node instance associated with this DataScopeNode.
- **Description**: The `DataScopeNode` class represents a node within the DataScope that is lazy-loaded from the database. It encapsulates a `Node` object and provides a method to retrieve a string identifier for the node, formatted as `{version_display_name}/{relative_path}`. This class is used to manage and access node data within a DataScope context.

**Methods**

---
#### DataScopeNode.__init__
The `__init__` function initializes a `DataScopeNode` instance with a given `Node` object.
- **Inputs**:
    - `node`: A `Node` object that represents a node within the `DataScope`.
- **Control Flow**:
    - Assigns the provided `Node` object to the instance variable `_node`.
- **Output**:
    - The function does not return any value; it initializes the instance with the provided `Node`.


---
#### DataScopeNode.get_identifier
The `get_identifier` function returns a string identifier for a node, formatted as `{version_display_name}/{relative_path}`.
- **Inputs**:
    - None
- **Control Flow**:
    - Retrieve the `version_display_name` from the node's version attribute.
    - Return a formatted string combining `version_display_name` and the node's `relative_path`.
- **Output**:
    - A string identifier in the format `{version_display_name}/{relative_path}`.


---
#### DataScopeNode.node
The `node` function is a property method that returns the private `_node` attribute of a `DataScopeNode` instance.
- **Inputs**:
    - None
- **Control Flow**:
    - The function is a property method, which means it is accessed like an attribute rather than a method call.
    - It directly returns the `_node` attribute of the `DataScopeNode` instance.
- **Output**:
    - The function returns an instance of the `Node` class, which is stored in the `_node` attribute of the `DataScopeNode` instance.



