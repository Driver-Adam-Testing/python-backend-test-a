# Purpose
This Python source code file defines a set of SQLAlchemy ORM models using the `sqlmodel` library, which is an extension of SQLAlchemy and Pydantic. The primary purpose of this file is to define the database schema and relationships for a system that manages assets, versions, nodes, and related entities. The code includes several classes, each representing a table in the database, such as `PrimaryAsset`, `Version`, `Node`, `UserCache`, and others. These classes define fields that correspond to columns in the database tables, including primary keys, foreign keys, and various data types. The relationships between these tables are also defined, allowing for complex queries and operations on the data.

The file provides a comprehensive and structured approach to managing data related to assets and their versions, including metadata, relationships, and historical data. It includes features such as indexing for efficient querying, computed columns for derived data, and cascading operations for maintaining referential integrity. The code is designed to be part of a larger application, likely serving as a backend component that interacts with a PostgreSQL database. It does not define public APIs or external interfaces directly but rather serves as a foundational layer for data persistence and retrieval within the application.
# Imports and Dependencies

---
- `hashlib`
- `uuid`
- `datetime`
- `TYPE_CHECKING`
- `Optional`
- `UUID`
- `database.models_v2_enums.AutoDocStatusMessageKind`
- `database.models_v2_enums.LlmPipelineKind`
- `database.models_v2_enums.NodeKind`
- `database.models_v2_enums.PrimaryAssetKind`
- `database.models_v2_enums.VersionStatus`
- `sqlalchemy.Column`
- `sqlalchemy.Computed`
- `sqlalchemy.DateTime`
- `sqlalchemy.Index`
- `sqlalchemy.Integer`
- `sqlalchemy.desc`
- `sqlalchemy.func`
- `sqlalchemy.dialects.postgresql.JSONB`
- `sqlmodel.Field`
- `sqlmodel.Relationship`
- `sqlmodel.SQLModel`


# Global Variables

---
### __table_args__ 
- **Type**: `tuple`
- **Description**: The `__table_args__` variable is a tuple that contains additional arguments for the SQLAlchemy table configuration. In this code, it is used to define indexes for the SQL tables, ensuring unique constraints and optimizing query performance.
- **Use**: This variable is used to specify additional table-level options, such as indexes, for the SQLAlchemy ORM models.


---
### __tablename__ 
- **Type**: `str`
- **Description**: The `__tablename__` variable is a string that specifies the name of the database table associated with a SQLModel class. It is used in SQLAlchemy ORM to map the class to a specific table in the database.
- **Use**: This variable is used to define the table name for each SQLModel class, ensuring that the ORM knows which table to interact with for database operations.


---
### codebase_settings_auto_commit_docs 
- **Type**: `Optional[bool]`
- **Description**: The `codebase_settings_auto_commit_docs` variable is a field in the `PrimaryAsset` class, which is part of a SQLModel ORM mapping to a database table. It is an optional boolean that indicates whether the automatic commit of documentation is enabled for a particular primary asset.
- **Use**: This variable is used to store and retrieve the setting for automatic documentation commits within the `PrimaryAsset` database table.


---
### contents 
- **Type**: `list[DerivedContent]`
- **Description**: The `contents` variable is a relationship attribute in the `Node` class, which is part of a SQLModel ORM mapping to a database table. It represents a list of `DerivedContent` objects associated with a particular `Node` instance.
- **Use**: This variable is used to manage and access the related `DerivedContent` entries for a `Node`, with cascading delete operations and passive deletes enabled.


---
### created_at 
- **Type**: `Optional[datetime]`
- **Description**: The `created_at` variable is a field in several SQLModel classes, such as `PrimaryAsset`, `Version`, `Node`, `RuntimeLlmSession`, `RuntimeLlmMessageHistory`, `RuntimeLlmMessage`, and `AutoDocStatusHistory`. It is of type `None | datetime`, meaning it can either be a `datetime` object or `None`. This field is automatically set to the current timestamp when a new record is created, thanks to the `server_default=func.now()` setting in the SQLAlchemy `Column` definition.
- **Use**: This variable is used to store the timestamp of when a record was created in the database.


---
### created_versions 
- **Type**: `list["Version"]`
- **Description**: The `created_versions` variable is a list of `Version` objects associated with a user in the `UserCache` class. It represents the versions that a particular user has created.
- **Use**: This variable is used to establish a relationship between users and the versions they have created, allowing for tracking and management of version creation by users.


---
### creator 
- **Type**: ``UserCache``
- **Description**: The `creator` variable is a relationship attribute in the `Version` class that links a version to its creator, represented by the `UserCache` class. This relationship is established through a secondary table `version_creator`, which associates versions with users who created them.
- **Use**: This variable is used to identify and access the user who created a particular version of an asset.


---
### depth 
- **Type**: `int`
- **Description**: The `depth` variable is an integer field within the `Node` class, representing the depth of a node in a hierarchical structure. It is computed based on the number of slashes in the `relative_path` attribute, which indicates the node's position in the hierarchy.
- **Use**: This variable is used to determine the hierarchical level of a node within a version's structure, facilitating operations like ancestor searching and root node identification.


---
### display_name 
- **Type**: `str`
- **Description**: The `display_name` variable is a string field used in both the `PrimaryAsset` and `Version` classes. It serves as an indexed field, allowing for efficient querying and retrieval of records based on this attribute.
- **Use**: This variable is used to store and index the display name of primary assets and versions, ensuring uniqueness in combination with other fields.


---
### document_sources 
- **Type**: `list["DocumentSource"]`
- **Description**: The `document_sources` variable is a list of `DocumentSource` objects associated with a `Node` in the database model. It represents the sources of documents that are linked to a particular node, allowing for the management and retrieval of document-related data within the system.
- **Use**: This variable is used to establish a relationship between a `Node` and its associated document sources, enabling operations such as cascading deletes and orphan removal.


---
### id 
- **Type**: `UUID`
- **Description**: The `id` variable is a globally defined field in several classes, such as `PrimaryAsset`, `Node`, `RuntimeLlmSession`, `RuntimeLlmMessageHistory`, `RuntimeLlmMessage`, and `AutoDocStatusHistory`. It is of type `UUID` and is used as a primary key for these tables, ensuring each entry has a unique identifier. The `id` field is automatically generated using `uuid.uuid4` as the default factory, which provides a random UUID.
- **Use**: This variable is used to uniquely identify records in the database tables associated with each class.


---
### inspector_runs 
- **Type**: `list`
- **Description**: The `inspector_runs` variable is a list of `InspectorRun` objects associated with a `Version` instance. It represents the collection of inspection runs that have been executed for a particular version of a primary asset.
- **Use**: This variable is used to maintain and access the history of inspection runs for a specific version, ordered by their update time in descending order.


---
### installation_id 
- **Type**: `UUID | None`
- **Description**: The `installation_id` is a field in the `PrimaryAsset` class, which represents a unique identifier for a Git provider app installation. It is of type `UUID` and can be `None`, indicating that it may not always be set for a `PrimaryAsset` instance.
- **Use**: This variable is used to associate a `PrimaryAsset` with a specific Git provider app installation, allowing for integration and management of assets within a version control system.


---
### kind 
- **Type**: `PrimaryAssetKind`
- **Description**: The `kind` variable is a field in the `PrimaryAsset` class, which is a SQLModel representing a primary asset in the database. It is of type `PrimaryAssetKind`, which is likely an enumeration imported from `database.models_v2_enums`. This field is indexed in the database, suggesting it is used frequently in queries.
- **Use**: This variable is used to categorize or specify the type of primary asset within the database model.


---
### llm_message_json 
- **Type**: `dict | None`
- **Description**: The `llm_message_json` variable is a field in the `RuntimeLlmMessage` class, which is a SQLModel table representing a message in a runtime LLM session. This variable is defined as a dictionary or None, and it is stored in a JSONB column in a PostgreSQL database, allowing for flexible storage of JSON data.
- **Use**: This variable is used to store the JSON representation of a message within a runtime LLM session, allowing for structured data to be saved and retrieved as part of the message history.


---
### llm_session 
- **Type**: ``RuntimeLlmSession``
- **Description**: The `llm_session` variable is an instance of the `RuntimeLlmSession` class, which represents a session for a runtime large language model (LLM). This class is defined as a table in the database with fields such as `id`, `user_id`, `organization_id`, `source_node_ids_str`, `page_node_id`, `created_at`, and `updated_at`. It also includes a relationship to `RuntimeLlmMessageHistory`, indicating that each session can have multiple message histories associated with it.
- **Use**: This variable is used to manage and store information about individual LLM sessions, including their creation and update timestamps, and to link them with their respective message histories.


---
### llm_session_id 
- **Type**: `UUID`
- **Description**: The `llm_session_id` is a UUID field that serves as a foreign key linking a message history entry to a specific runtime LLM session. It ensures that each message history is associated with the correct session, allowing for organized tracking of interactions within a session.
- **Use**: This variable is used to associate a message history with its corresponding runtime LLM session in the database.


---
### message_histories 
- **Type**: `list`
- **Description**: The `message_histories` variable is a list of `RuntimeLlmMessageHistory` objects associated with a `RuntimeLlmSession`. Each `RuntimeLlmMessageHistory` represents a collection of messages exchanged during a specific session of a runtime LLM (Language Model) interaction.
- **Use**: This variable is used to store and manage the history of messages for a given LLM session, allowing for tracking and retrieval of past interactions.


---
### message_history 
- **Type**: `list["RuntimeLlmMessageHistory"]`
- **Description**: The `message_history` variable is a list of `RuntimeLlmMessageHistory` objects. Each `RuntimeLlmMessageHistory` instance represents a collection of messages associated with a specific LLM (Language Model) session. This structure is used to track the sequence of messages exchanged during a session.
- **Use**: This variable is used to store and manage the history of messages for each LLM session, allowing for retrieval and analysis of past interactions.


---
### message_history_id 
- **Type**: `UUID`
- **Description**: The `message_history_id` is a UUID field in the `RuntimeLlmMessage` class, which serves as a foreign key linking each message to its corresponding message history in the `RuntimeLlmMessageHistory` table. This field ensures that each message is associated with a specific message history, allowing for organized tracking and retrieval of messages within a session.
- **Use**: This variable is used to associate a message with its corresponding message history in the database.


---
### messages 
- **Type**: `list["RuntimeLlmMessage"]`
- **Description**: The `messages` variable is a list of `RuntimeLlmMessage` objects, which are part of the `RuntimeLlmMessageHistory` class. This list represents the collection of messages associated with a particular message history in a runtime LLM (Language Model) session.
- **Use**: This variable is used to store and manage the sequence of messages exchanged during a specific LLM session, ordered by their creation time.


---
### misc_metadata 
- **Type**: `dict | None`
- **Description**: The `misc_metadata` variable is a dictionary that can store miscellaneous metadata related to a `Node` object. It is defined as a JSONB column in the database, allowing for flexible storage of key-value pairs. The variable is optional, meaning it can be `None` if no metadata is provided.
- **Use**: This variable is used to store additional metadata for a `Node` that does not fit into the predefined schema, allowing for extensibility and custom data storage.


---
### most_recent_version 
- **Type**: `Optional["Version"]`
- **Description**: The `most_recent_version` variable is a relationship attribute in the `PrimaryAsset` class, which represents the most recent version of a primary asset. It is defined as an optional relationship to the `Version` class, indicating that a primary asset may or may not have a most recent version associated with it.
- **Use**: This variable is used to access the most recent version of a primary asset, ordered by the `updated_at` timestamp in descending order.


---
### nodes 
- **Type**: `list[Node]`
- **Description**: The `nodes` variable is a list of `Node` objects associated with a `Version` instance in the database model. Each `Node` represents a specific element or component within a version, identified by its unique attributes such as `id`, `kind`, `version_id`, and `relative_path`. The `nodes` list is managed through a SQLModel relationship, allowing for operations like cascading deletes and passive deletes.
- **Use**: This variable is used to maintain and manage the collection of `Node` instances that are linked to a specific `Version`, facilitating database operations and ensuring data integrity.


---
### organization_id 
- **Type**: `str`
- **Description**: The `organization_id` is a string field used in multiple tables within the database schema, such as `PrimaryAsset` and `RuntimeLlmSession`. It serves as an identifier for organizations, allowing for the association of various records with a specific organization.
- **Use**: This variable is used to index and uniquely identify records related to an organization across different tables in the database.


---
### page_node_id 
- **Type**: `UUID | None`
- **Description**: The `page_node_id` is a global variable defined as a field in the `RuntimeLlmSession` class. It is of type `UUID` or `None`, indicating that it can either hold a universally unique identifier or be null. This field is used to store the identifier of a page node associated with a runtime LLM session.
- **Use**: This variable is used to reference a specific page node within a runtime LLM session, allowing for the association of session data with a particular node in the system.


---
### page_sources 
- **Type**: `list`
- **Description**: The `page_sources` variable is a list of `DocumentSource` objects associated with a `Node` in the database model. It represents the relationship between a node and its page sources, which are likely documents or data sources linked to that node.
- **Use**: This variable is used to manage and access the collection of `DocumentSource` objects related to a specific node, facilitating operations like cascading deletes and orphan removal.


---
### pipeline_kind 
- **Type**: `str`
- **Description**: The `pipeline_kind` variable is a string field within the `RuntimeLlmMessageHistory` class, which is part of a SQLModel table. It is used to specify the kind of pipeline associated with a particular message history in a runtime LLM (Language Model) session.
- **Use**: This variable is used to index and categorize message histories based on the type of LLM pipeline they are associated with, defaulting to `LlmPipelineKind.DEFAULT`.


---
### previous_version_id 
- **Type**: `UUID | None`
- **Description**: The `previous_version_id` is a field in the `Version` class that stores the UUID of the preceding version of a given asset. It is nullable, meaning it can be set to `None` if there is no previous version.
- **Use**: This variable is used to establish a link to the previous version of an asset, allowing for version tracking and history management.


---
### primary_asset 
- **Type**: `PrimaryAsset`
- **Description**: The `PrimaryAsset` class represents a primary asset in the system, which is a key entity that can have multiple versions and is associated with an organization. It includes fields for unique identification, display name, repository and organization IDs, and timestamps for creation and updates. The class also manages relationships with versions and tags, allowing for the organization and categorization of assets.
- **Use**: This variable is used to define and manage the primary assets within the system, facilitating version control and asset categorization.


---
### primary_asset_id 
- **Type**: `UUID`
- **Description**: The `primary_asset_id` is a UUID field that serves as a foreign key linking a version to its corresponding primary asset in the database. It is a crucial identifier for associating a version with its primary asset, ensuring data integrity and relational mapping between these entities.
- **Use**: This variable is used to establish a relationship between a version and its primary asset, allowing for efficient querying and data management within the database.


---
### related_content_last_updated 
- **Type**: `Optional[datetime]`
- **Description**: The `related_content_last_updated` variable is a field in the `PrimaryAsset` class, which is a SQLModel representing a table in a database. This field stores a timestamp indicating the last time related content was updated for a primary asset. It is defined as an optional datetime, meaning it can be null if no updates have been recorded.
- **Use**: This variable is used to track the last update time of related content for a primary asset in the database.


---
### relative_path 
- **Type**: `str`
- **Description**: The `relative_path` variable is a string field in the `Node` class, representing the path relative to a certain base directory or root. It is a non-nullable field and is indexed for efficient querying. The `relative_path` is used to uniquely identify the location of a node within a version.
- **Use**: This variable is used to store and index the relative path of a node within a version, facilitating unique identification and efficient querying.


---
### root_node 
- **Type**: `Optional[`Node`]`
- **Description**: The `root_node` variable is a relationship attribute in the `Version` class, representing the root node of a version. It is defined as an optional relationship to the `Node` class, where the node has a depth of 0, indicating it is the root of the node hierarchy for that version.
- **Use**: This variable is used to access the root node of a version, which is the starting point of the node hierarchy within that version.


---
### source_node_ids_str 
- **Type**: `str | None`
- **Description**: The `source_node_ids_str` variable is a string or None type field in the `RuntimeLlmSession` class. It is designed to store a string representation of source node IDs, which may be used to track or reference specific nodes within a session. The field is nullable, allowing it to be set to None if no source node IDs are applicable or available.
- **Use**: This variable is used to store and manage the string representation of source node IDs within a runtime LLM session, facilitating node tracking or referencing.


---
### status 
- **Type**: `VersionStatus`
- **Description**: The `status` variable is a field in the `Version` class, which is a SQLModel table representing a version of a primary asset. It is of type `VersionStatus`, an enumeration that likely defines various states a version can be in, such as 'GENERATING', 'GENERATION_ERROR', or 'GENERATION_COMPLETE'. This field is indexed for efficient querying.
- **Use**: This variable is used to track and query the current state of a version within the database.


---
### status_kind 
- **Type**: `AutoDocStatusMessageKind`
- **Description**: The `status_kind` variable is a field in the `AutoDocStatusHistory` class, which is a SQLModel table. It is of type `AutoDocStatusMessageKind`, an enumeration imported from `database.models_v2_enums`. This field is non-nullable, indicating that every record in the `v2_autodoc_status_history` table must have a defined status kind.
- **Use**: This variable is used to store the kind of status message associated with an autodoc status history entry, ensuring that each entry has a specific status type.


---
### tag_id 
- **Type**: `UUID`
- **Description**: The `tag_id` variable is a UUID field defined within the `PrimaryAssetTag` class, which is a SQLModel table representing a many-to-many relationship between primary assets and tags. It serves as a primary key and is indexed for efficient querying.
- **Use**: This variable is used to uniquely identify a tag associated with a primary asset in the database.


---
### tags 
- **Type**: `list["Tag"]`
- **Description**: The `tags` variable is a relationship attribute in the `PrimaryAsset` class, which is a SQLModel class representing a table in a database. It defines a many-to-many relationship between `PrimaryAsset` and `Tag` entities, allowing each primary asset to be associated with multiple tags.
- **Use**: This variable is used to manage and access the tags associated with a primary asset in the database.


---
### total_files 
- **Type**: `int | None`
- **Description**: The `total_files` variable is an optional integer field within the `Node` class, representing the total number of files associated with a particular node. It is computed from the `misc_metadata` JSONB column, specifically extracting the 'total_files' key and converting it to an integer. This field is indexed and can be null, indicating that the total number of files is not always available or applicable.
- **Use**: This variable is used to store and retrieve the total number of files related to a node, facilitating efficient querying and indexing within the database.


---
### updated_at 
- **Type**: `Optional[datetime]`
- **Description**: The `updated_at` variable is a field in several SQLModel classes, such as `PrimaryAsset`, `Version`, `Node`, `RuntimeLlmSession`, and `RuntimeLlmMessage`. It is of type `Optional[datetime]` and is used to store the timestamp of the last update made to the record. The field is automatically updated to the current time whenever the record is modified, thanks to the `onupdate=func.now()` parameter in its SQLAlchemy column definition.
- **Use**: This variable is used to track the last modification time of a record in the database, ensuring that the data reflects the most recent changes.


---
### user_id 
- **Type**: `str`
- **Description**: The `user_id` variable is a string that serves as a foreign key reference to the `id` field in the `user_cache` table. It is used to associate a user with various entities, such as versions and runtime sessions, within the database schema.
- **Use**: This variable is used to link user-related data across different tables, ensuring referential integrity and enabling user-specific operations.


---
### version 
- **Type**: `str`
- **Description**: The `version` variable is a global string variable that likely holds the version information of the software or a specific component within the codebase. It is typically used to track the current version of the application or module, which can be important for compatibility and update management.
- **Use**: This variable is used to store and provide access to the version information of the software or component.


---
### version_id 
- **Type**: `UUID`
- **Description**: The `version_id` is a UUID field that serves as a primary key in the `VersionCreator` class. It is used to uniquely identify a version within the `v2_version` table in the database.
- **Use**: This variable is used to establish a relationship between a version and its creator in the `version_creator` table, allowing for tracking of which user created which version.


---
### versions 
- **Type**: `list["Version"]`
- **Description**: The `versions` variable is a list of `Version` objects associated with a `PrimaryAsset`. It represents all the versions of a particular primary asset in the system. Each `Version` object in the list contains details about a specific version, such as its display name, status, and timestamps for creation and updates.
- **Use**: This variable is used to maintain and access the collection of all versions related to a specific primary asset, allowing for operations like retrieval, ordering, and cascading deletions.


# Classes

---
### AutoDocStatusHistory 
- **Type**: `class`
- **Members**:
    - `id`: A unique identifier for each AutoDocStatusHistory entry, generated by default.
    - `page_node_id`: References the associated node in the database, ensuring referential integrity.
    - `status_kind`: Indicates the type of status message associated with the AutoDoc process.
    - `content`: Optional field to store additional information or message content.
    - `created_at`: Timestamp indicating when the status history entry was created, with a default value of the current time.
    - `call_id`: Optional identifier for tracking the specific call or process instance related to this status entry.
- **Description**: The AutoDocStatusHistory class is a SQLModel-based table representation that logs the history of status messages related to the AutoDoc process. It includes fields for unique identification, association with a specific node, the kind of status message, optional content, creation timestamp, and an optional call identifier. This class is designed to maintain a historical record of status changes for documentation automation processes, supporting database operations with referential integrity and automatic timestamping.
- **Inherits From**:
    - SQLModel


---
### Node 
- **Type**: `class`
- **Members**:
    - `id`: A unique identifier for the node, generated by default.
    - `kind`: Specifies the type of node, represented by the NodeKind enum.
    - `version_id`: References the version this node belongs to, with a foreign key constraint.
    - `relative_path`: Stores the path relative to the version's root, used for indexing.
    - `depth`: Calculated depth of the node based on its relative path.
    - `total_files`: Optional field indicating the total number of files, derived from misc_metadata.
    - `misc_metadata`: Optional dictionary for storing additional metadata in JSONB format.
    - `created_at`: Timestamp of when the node was created, with a default value of the current time.
    - `updated_at`: Timestamp of the last update to the node, automatically updated on changes.
    - `version`: Relationship to the Version class, linking nodes to their version.
    - `contents`: List of DerivedContent objects related to this node, with cascading delete behavior.
    - `document_sources`: List of DocumentSource objects where this node is the source, with cascading delete behavior.
    - `page_sources`: List of DocumentSource objects where this node is a page, with cascading delete behavior.
    - `s3_url`: Property that generates an S3 URL for accessing the node's content.
- **Description**: The Node class represents a node in a versioned data structure, storing information about its type, path, and associated metadata. It includes relationships to other entities such as versions, contents, and document sources, and provides indexing for efficient querying. The class also features computed properties for depth and total files, and a method to generate an S3 URL for accessing node content.
- **Inherits From**:
    - SQLModel

**Methods**

---
#### Node.s3_url
The `s3_url` function generates a URL for accessing a file stored in an S3 bucket, based on the organization ID, primary asset ID, version ID, and relative path.
- **Inputs**:
    - None
- **Control Flow**:
    - The function computes a SHA-256 hash of the organization ID from the primary asset associated with the version, and truncates it to 63 characters.
    - It constructs an S3 URL using the hashed organization ID, primary asset ID, version ID, and relative path.
    - The constructed URL is returned as a string.
- **Output**:
    - A string representing the S3 URL for the specified file.



---
### PrimaryAsset 
- **Type**: `class`
- **Members**:
    - `id`: A unique identifier for the primary asset, generated by default using UUID.
    - `display_name`: The display name of the primary asset, indexed for quick lookup.
    - `repository_id`: An optional identifier for the repository associated with the primary asset.
    - `organization_id`: The identifier for the organization to which the primary asset belongs, indexed for quick lookup.
    - `kind`: The type of primary asset, defined by the PrimaryAssetKind enumeration, and indexed for quick lookup.
    - `installation_id`: An optional UUID referencing the installation in the git provider app, with foreign key constraints.
    - `codebase_settings_auto_commit_docs`: An optional boolean indicating if auto-commit for documentation is enabled, temporarily stored here.
    - `created_at`: The timestamp when the primary asset was created, with a server default of the current time.
    - `updated_at`: The timestamp when the primary asset was last updated, automatically updated to the current time.
    - `related_content_last_updated`: An optional timestamp indicating the last update time of related content.
    - `most_recent_version`: A relationship to the most recent version of the primary asset, with specific join and cascade rules.
    - `versions`: A list of all versions associated with the primary asset, with specific join, cascade, and order rules.
    - `tags`: A list of tags associated with the primary asset, using a secondary table for the relationship.
- **Description**: The `PrimaryAsset` class represents a primary asset in a database, with attributes for identification, organization, and type, as well as timestamps for creation and updates. It includes relationships to versions and tags, allowing for complex associations and operations within a SQLModel-based ORM framework. The class is designed to be part of a larger system managing assets, versions, and their metadata, with support for indexing and foreign key constraints to ensure data integrity and efficient querying.
- **Inherits From**:
    - SQLModel


---
### PrimaryAssetTag 
- **Type**: `class`
- **Members**:
    - `tag_id`: A UUID field that serves as a primary key and foreign key to the tags table.
    - `primary_asset_id`: A UUID field that serves as a primary key and foreign key to the v2_primary_asset table.
- **Description**: The `PrimaryAssetTag` class is a SQLModel-based table representation that establishes a many-to-many relationship between primary assets and tags. It uses two UUID fields, `tag_id` and `primary_asset_id`, both of which are indexed and serve as primary keys, to link entries in the `tags` table and the `v2_primary_asset` table, respectively. This class facilitates the association of multiple tags with a primary asset and vice versa, enabling efficient querying and management of asset-tag relationships in the database.
- **Inherits From**:
    - SQLModel


---
### RuntimeLlmMessage 
- **Type**: `class`
- **Members**:
    - `id`: A unique identifier for the message, generated by default using UUID.
    - `message_history_id`: References the ID of the associated message history, with a foreign key constraint.
    - `llm_message_hash`: Stores a hash of the LLM message for integrity or identification purposes.
    - `llm_message_json`: Holds the JSON representation of the LLM message, which can be nullable.
    - `created_at`: Timestamp indicating when the message was created, with a default value set to the current time.
    - `updated_at`: Timestamp indicating when the message was last updated, automatically updated to the current time.
    - `message_history`: Defines a relationship to the RuntimeLlmMessageHistory class, linking messages to their history.
- **Description**: The RuntimeLlmMessage class is a SQLModel-based ORM class that represents a message in a runtime LLM (Large Language Model) system. It is designed to store and manage individual messages, including their unique identifiers, associated message history, and JSON content. The class also tracks creation and update timestamps, and it establishes a relationship with the RuntimeLlmMessageHistory class to maintain the context of message sequences. This class is part of a larger database schema for managing LLM sessions and their associated data.
- **Inherits From**:
    - SQLModel


---
### RuntimeLlmMessageHistory 
- **Type**: `class`
- **Members**:
    - `id`: A unique identifier for each message history entry.
    - `llm_session_id`: References the associated LLM session.
    - `pipeline_kind`: Indicates the type of LLM pipeline used.
    - `messages`: A list of messages associated with this message history.
    - `llm_session`: The LLM session to which this message history belongs.
- **Description**: The `RuntimeLlmMessageHistory` class is a SQLModel-based ORM class that represents a table for storing the history of messages exchanged during a runtime LLM session. It includes fields for a unique identifier, a reference to the associated LLM session, the kind of pipeline used, and relationships to the messages and session. This class facilitates the organization and retrieval of message histories in a structured database format, supporting operations like indexing and cascading deletions.
- **Inherits From**:
    - SQLModel


---
### RuntimeLlmSession 
- **Type**: `class`
- **Members**:
    - `id`: A unique identifier for the session, generated by default using UUID.
    - `user_id`: The identifier for the user associated with the session, indexed for quick lookup.
    - `organization_id`: The identifier for the organization associated with the session, indexed for quick lookup.
    - `source_node_ids_str`: A string representing source node IDs, which can be null.
    - `page_node_id`: A UUID representing the page node ID, which can be null.
    - `created_at`: The timestamp when the session was created, with a default value set to the current time.
    - `updated_at`: The timestamp when the session was last updated, automatically updated to the current time.
    - `message_histories`: A list of message histories associated with the session, establishing a relationship with the RuntimeLlmMessageHistory class.
- **Description**: The RuntimeLlmSession class represents a session for a runtime large language model (LLM) interaction, storing essential metadata such as user and organization identifiers, node references, and timestamps for creation and updates. It also maintains a relationship with message histories, allowing for the tracking of interactions within the session.
- **Inherits From**:
    - SQLModel


---
### UserCache 
- **Type**: `class`
- **Members**:
    - `id`: This is the primary key and represents the auth0 ID in the form 'auth0|1234567890'.
    - `full_name`: Stores the full name of the user.
    - `email`: Stores the email address of the user.
    - `created_versions`: A list of Version objects that the user has created, establishing a relationship with the Version class.
- **Description**: The UserCache class is a SQLModel-based class that represents a cache of user information in a database table named 'user_cache'. It includes fields for storing a user's unique identifier (auth0 ID), full name, and email address. Additionally, it maintains a relationship with the Version class, allowing for the association of multiple versions created by the user. This class is designed to facilitate the management and retrieval of user-related data within the context of a version control system.
- **Inherits From**:
    - SQLModel


---
### Version 
- **Type**: `class`
- **Members**:
    - `id`: A unique identifier for the version, generated by default.
    - `primary_asset_id`: References the primary asset associated with this version, with a foreign key constraint.
    - `display_name`: The display name of the version.
    - `status`: The current status of the version, indexed for quick access.
    - `previous_version_id`: References the previous version, if any, with a foreign key constraint.
    - `created_at`: Timestamp indicating when the version was created, with a default value of the current time.
    - `updated_at`: Timestamp indicating when the version was last updated, automatically updated to the current time.
    - `primary_asset`: Relationship to the PrimaryAsset class, linking versions to their primary asset.
    - `nodes`: A list of Node objects associated with this version, with cascading delete behavior.
    - `creator`: Relationship to the UserCache class, representing the user who created this version.
    - `root_node`: An optional relationship to the root Node of this version, view-only.
    - `inspector_runs`: A list of InspectorRun objects associated with this version, ordered by update time.
    - `browsable`: A property indicating if the version is in a browsable state based on its status.
- **Description**: The Version class represents a version of a primary asset in a database model, providing fields for unique identification, status tracking, and timestamps for creation and updates. It establishes relationships with other entities such as PrimaryAsset, Node, UserCache, and InspectorRun, facilitating complex interactions and dependencies. The class includes indexing for efficient querying and supports cascading operations for related entities. Additionally, it features a property to determine if the version is in a state that allows browsing.
- **Inherits From**:
    - SQLModel

**Methods**

---
#### Version.browsable
The `browsable` function checks if the current version's status allows it to be browsed.
- **Inputs**:
    - None
- **Control Flow**:
    - The function checks if the `status` attribute of the `Version` instance is one of the specified statuses: `GENERATING`, `GENERATION_ERROR`, or `GENERATION_COMPLETE`.
    - If the `status` is in the specified set, the function returns `True`; otherwise, it returns `False`.
- **Output**:
    - A boolean value indicating whether the version is in a state that allows it to be browsed.



---
### VersionCreator 
- **Type**: `class`
- **Members**:
    - `version_id`: A UUID field that serves as a primary key and foreign key to the 'v2_version' table.
    - `user_id`: A string field that serves as a foreign key to the 'user_cache' table.
- **Description**: The `VersionCreator` class is a SQLModel-based table that establishes a relationship between versions and users, indicating which user created a particular version. It uses two fields, `version_id` and `user_id`, both of which are indexed and have cascading delete behavior, ensuring that when a version or user is deleted, the corresponding entries in this table are also removed.
- **Inherits From**:
    - SQLModel


