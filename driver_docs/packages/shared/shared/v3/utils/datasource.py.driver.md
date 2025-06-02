# Purpose
The provided Python code defines a class named `DataSource` using the Pydantic library, which is designed to manage and validate a collection of node identifiers (`node_ids`) associated with a specific organization. The primary purpose of this class is to facilitate the retrieval and caching of `Node` objects from a database, ensuring that all node IDs belong to the specified organization. The class includes several factory methods for constructing a `DataSource` instance from different types of input, such as node IDs, page node IDs, and relative paths. These methods utilize SQLAlchemy and SQLModel to perform database queries, ensuring that the data integrity is maintained by checking the association of node IDs with the given organization.

The `DataSource` class also provides functionality to describe the contents of the data source by organizing nodes into a hierarchical structure based on their relative paths and versions. This is achieved through methods like `describe_contents` and `describe_contents_char_limit`, which generate a textual representation of the nodes, grouped by version and optionally limited by tree depth. The class uses caching to optimize performance by storing previously fetched `Node` objects, reducing the need for repeated database queries. Overall, this code serves as a utility for managing and describing collections of nodes within an organizational context, with a focus on data validation and efficient data retrieval.
# Imports and Dependencies

---
- `uuid`
- `collections.defaultdict`
- `database.db.get_session`
- `database.models_v1.DocumentSource`
- `database.models_v2.Node`
- `database.models_v2.PrimaryAsset`
- `database.models_v2.Version`
- `database.models_v2_enums.NodeKind`
- `pydantic.BaseModel`
- `pydantic.Field`
- `pydantic.PrivateAttr`
- `sqlalchemy.orm.selectinload`
- `sqlmodel.and_`
- `sqlmodel.or_`
- `sqlmodel.select`


# Global Variables

---
### _cached_nodes 
- **Type**: `list[Node] | None`
- **Description**: The `_cached_nodes` variable is a private attribute of the `DataSource` class, designed to store a list of `Node` objects. It is initially set to `None` and is used to cache the nodes associated with the `DataSource` to avoid repeated database fetches.
- **Use**: This variable is used to store and cache the `Node` objects for a `DataSource`, improving performance by reducing the need for repeated database queries.


---
### node_ids 
- **Type**: `list[uuid.UUID]`
- **Description**: The `node_ids` variable is a list of UUIDs that represent unique identifiers for nodes within a data source. These nodes are associated with a specific organization, as indicated by the `organization_id`. The list is initialized as an empty list by default.
- **Use**: This variable is used to store and manage the identifiers of nodes that belong to a particular organization within the `DataSource` class.


# Classes

---
### DataSource 
- **Type**: `class`
- **Members**:
    - `node_ids`: A list of UUIDs representing node IDs associated with a single organization.
    - `organization_id`: A string representing the ID of the organization to which the node IDs belong.
    - `_cached_nodes`: A private attribute that caches the Node objects to avoid re-fetching them on every access.
- **Description**: The `DataSource` class is designed to manage a collection of node IDs that are associated with a single organization, providing functionality to cache the underlying Node objects for efficiency. It includes methods to initialize the data source with node IDs, validate their association with the organization, and retrieve nodes from various sources such as node IDs, page IDs, or relative paths. The class also offers methods to describe the contents of the data source, grouping nodes by version and optionally limiting the depth of the directory tree displayed. This class is built on top of the Pydantic `BaseModel` and utilizes SQLAlchemy for database interactions.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### DataSource.__init__
The `__init__` function initializes a `DataSource` object by validating that all provided `node_ids` belong to the specified `organization_id` and raises an error if any do not.
- **Inputs**:
    - `node_ids`: A list of UUIDs representing node identifiers that are expected to belong to the specified organization.
    - `organization_id`: A string representing the unique identifier of the organization to which the node_ids should belong.
- **Control Flow**:
    - The function begins by calling the superclass initializer with the provided `node_ids` and `organization_id`.
    - It checks if `node_ids` is not empty, and if so, it opens a database session using `get_session()`.
    - A SQL query is constructed to select node IDs from the database that match the provided `node_ids` and belong to the specified `organization_id`.
    - The query is executed, and the resulting list of matching IDs is compared to the original list of `node_ids`.
    - If the number of matching IDs does not equal the number of provided `node_ids`, a `ValueError` is raised indicating a mismatch.
    - Finally, the `_cached_nodes` attribute is initialized to `None`.
- **Output**:
    - The function does not return any value; it initializes the `DataSource` object and may raise a `ValueError` if validation fails.


---
#### DataSource.describe_contents
The `describe_contents` function generates a hierarchical summary of the nodes in a DataSource, organized by version and optionally limited by tree depth.
- **Inputs**:
    - `tree_depth`: An optional integer specifying the maximum depth of the folder hierarchy to display; if None, no depth limit is applied.
- **Control Flow**:
    - Initialize an empty list `summary_lines` to store the summary output.
    - Define a helper function `build_tree` to construct a nested dictionary representing the folder and file structure from a list of nodes.
    - Define a helper function `count_files` to recursively count the number of file nodes in a given tree structure.
    - Define a helper function `traverse_tree` to recursively traverse the tree structure, appending folder and file information to `summary_lines`, respecting the `tree_depth` limit if specified.
    - Group nodes by their version using a defaultdict to avoid mixing versions in the summary.
    - For each version group, append a version header to `summary_lines`, build the tree structure using `build_tree`, and traverse it using `traverse_tree`.
    - Return the joined `summary_lines` as a single string.
- **Output**:
    - A string representing the hierarchical summary of the DataSource's contents, organized by version and folder structure.


---
#### DataSource.describe_contents_char_limit
The `describe_contents_char_limit` function generates a description of the DataSource's contents, grouping nodes by version and limiting the description to a specified character limit.
- **Inputs**:
    - `char_limit`: An integer specifying the maximum number of characters allowed in the description.
- **Control Flow**:
    - Initialize an empty string `description` and set `tree_depth` to 2.
    - Enter a while loop that continues until a break condition is met.
    - Within the loop, call `describe_contents` with the current `tree_depth` to generate a new description.
    - Check if the new description is the same as the current `description`; if so, break the loop.
    - If the length of the new description is within the `char_limit`, update `description` to the new description.
    - If the new description exceeds the `char_limit`, break the loop.
    - Increment `tree_depth` by 1 to explore deeper folder levels in the next iteration.
- **Output**:
    - A string representing the description of the DataSource's contents, constrained by the specified character limit.


---
#### DataSource.from_node_ids
The `from_node_ids` function is a class method that creates a `DataSource` instance using a list of node IDs and an organization ID.
- **Inputs**:
    - `cls`: The class `DataSource` itself, used to create an instance.
    - `node_ids`: A list of UUIDs representing the node IDs to be included in the `DataSource`.
    - `organization_id`: A string representing the organization ID to which the node IDs belong.
- **Control Flow**:
    - The function is a class method, indicated by the `cls` parameter, which refers to the `DataSource` class.
    - It constructs a new `DataSource` object by calling the class constructor with the provided `node_ids` and `organization_id`.
    - The newly created `DataSource` object is returned.
- **Output**:
    - The function returns an instance of the `DataSource` class initialized with the provided node IDs and organization ID.


---
#### DataSource.from_page_id
The `from_page_id` function creates a `DataSource` instance by retrieving node IDs associated with a given page node ID from the `DocumentSource` table.
- **Inputs**:
    - `page_node_id`: A UUID representing the page node ID used to query the `DocumentSource` table.
    - `organization_id`: A string representing the organization ID to associate with the `DataSource` instance.
- **Control Flow**:
    - The function begins by opening a database session using `get_session()`.
    - It constructs a SQL query to select entries from the `DocumentSource` table where the `page_node_id` matches the provided `page_node_id`.
    - The query is executed, and all matching `DocumentSource` entries are retrieved.
    - A list of `source_node_id` values is extracted from the retrieved `DocumentSource` entries.
    - A new `DataSource` instance is created using the list of node IDs and the provided `organization_id`.
    - The `DataSource` instance is returned as the output of the function.
- **Output**:
    - The function returns a `DataSource` instance initialized with node IDs retrieved from the `DocumentSource` table and the specified organization ID.


---
#### DataSource.from_relative_paths
The `from_relative_paths` function constructs a `DataSource` object by querying node IDs from a database based on given relative paths, organization ID, and an optional version ID.
- **Inputs**:
    - `relative_paths`: A list of strings representing the relative paths of nodes to be queried.
    - `organization_id`: A string representing the ID of the organization to which the nodes belong.
    - `version_id`: An optional string representing the version ID to filter the nodes; if not provided, the latest version is used.
- **Control Flow**:
    - A database session is initiated using `get_session()`.
    - A SQL query is constructed to select nodes by joining the `Node`, `Version`, and `PrimaryAsset` tables.
    - The query filters nodes whose `relative_path` is in the `relative_paths` list and whose `organization_id` matches the provided `organization_id`.
    - The query further filters nodes by `version_id` if provided, or selects the latest version if `version_id` is `None`.
    - The query is executed, and the resulting nodes are retrieved.
    - Node IDs are extracted from the retrieved nodes.
    - A `DataSource` object is instantiated with the extracted node IDs and the provided `organization_id`.
- **Output**:
    - Returns a `DataSource` object initialized with node IDs corresponding to the specified relative paths and organization ID.


---
#### DataSource.nodes
The `nodes` function retrieves and caches a list of Node objects associated with the DataSource, loading them from the database if they are not already cached.
- **Inputs**:
    - None
- **Control Flow**:
    - Check if `_cached_nodes` is `None`, indicating that the nodes need to be loaded from the database.
    - Open a database session using `get_session()`.
    - Execute a query to load all ancestor nodes associated with `self.node_ids` and their versions using `selectinload`.
    - For each ancestor, build a set of conditions to find descendant nodes based on version and path criteria.
    - If conditions exist, execute a query to load all descendant nodes that match any of the conditions.
    - Combine the ancestor and descendant nodes into a dictionary keyed by node ID to eliminate duplicates.
    - Store the list of unique Node objects in `_cached_nodes`.
    - Return the cached list of Node objects.
- **Output**:
    - A list of Node objects that are either retrieved from the cache or loaded from the database.



# Functions

---
### build_tree 
The `build_tree` function constructs a hierarchical tree structure from a list of `Node` objects based on their relative paths.
- **Inputs**:
    - `nodes`: A list of `Node` objects, each representing a file or directory with a relative path and a kind (either a directory or a file).
- **Control Flow**:
    - Initialize an empty tree structure with 'children' and 'files' keys.
    - Iterate over each node in the input list.
    - For each node, split its relative path into parts and traverse the tree structure accordingly.
    - If the current part is the last in the path and the node is a directory, add it to the 'children' of the current tree level.
    - If the current part is the last in the path and the node is a file, add it to the 'files' of the current tree level.
    - If the current part is not the last, ensure the part exists in 'children' and move deeper into the tree structure.
- **Output**:
    - A dictionary representing the tree structure, with nested 'children' dictionaries for directories and 'files' lists for files.


---
### count_files 
The `count_files` function recursively counts all file nodes in a hierarchical tree structure represented by a dictionary.
- **Inputs**:
    - `tree_data`: A dictionary representing a tree structure, where each node can have 'files' (a list of file nodes) and 'children' (a dictionary of child nodes).
- **Control Flow**:
    - Initialize a count with the number of files in the current node using `len(tree_data.get('files', []))`.
    - Iterate over each child node in `tree_data.get('children', {}).values()`.
    - For each child node, recursively call `count_files` and add the result to the count.
    - Return the total count of files.
- **Output**:
    - An integer representing the total number of file nodes in the tree.


---
### traverse_tree 
The `traverse_tree` function recursively traverses a hierarchical tree structure of files and folders, generating a summary of the contents with optional depth limitation.
- **Inputs**:
    - `tree_data`: A dictionary representing the hierarchical structure of files and folders, where 'children' contains subfolders and 'files' contains files at the current level.
    - `indent`: An integer representing the current level of indentation, used to format the output summary with appropriate spacing.
- **Control Flow**:
    - Sort and list all files at the current level of the tree, appending them to the summary with the specified indentation.
    - Iterate over each subfolder in the 'children' of the current tree level, sorted by folder name.
    - Check if the current depth exceeds the specified tree depth limit; if so, append a truncated view of the folder with a file count to the summary.
    - If the depth limit is not reached, append the folder name to the summary and recursively call `traverse_tree` on the subfolder with increased indentation.
- **Output**:
    - The function does not return any value; instead, it appends formatted summary lines to the `summary_lines` list, which is used to build a textual representation of the tree structure.


