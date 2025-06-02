# Purpose
The `node_schemas.py` file defines a series of data models using the Pydantic library, which is a popular choice for data validation and settings management in Python. These models are structured to represent various entities and their relationships within a system, such as primary assets, versions, nodes, users, tags, and content. The file is organized into sections that define schemas for reading data (both flat and detailed views) and for creating or updating data. The use of Pydantic's `BaseModel` allows for automatic data validation and serialization, making these models suitable for use in APIs or other data-driven applications.

The file provides a comprehensive set of schemas that cover a wide range of functionalities, from basic data retrieval to more complex operations involving nested relationships and metadata. The models are designed to be flexible and extensible, with the use of generic types and computed fields to handle dynamic data scenarios. The inclusion of both read and write schemas indicates that this file is intended to be part of a larger application, likely serving as a backend component that interfaces with a database or other data storage system. The use of UUIDs for identifying entities and the inclusion of timestamps for creation and updates suggest a focus on maintaining data integrity and traceability. Overall, the file serves as a foundational component for managing and interacting with structured data in a robust and scalable manner.
# Imports and Dependencies

---
- `datetime`
- `Generic`
- `TypeVar`
- `UUID`
- `ContentKind`
- `NodeKind`
- `PrimaryAssetKind`
- `BaseModel`
- `computed_field`


# Global Variables

---
### T 
- **Type**: `TypeVar`
- **Description**: `T` is a type variable used in generic programming to allow for type flexibility in class definitions. It is defined using Python's `TypeVar` from the `typing` module, which enables the creation of generic classes or functions that can operate on any data type.
- **Use**: `T` is used as a placeholder for any data type in the `ListWithCount` class, allowing it to handle lists of any type.


---
### codebase_settings_auto_commit_docs 
- **Type**: `bool | None`
- **Description**: The `codebase_settings_auto_commit_docs` variable is a boolean field that indicates whether the automatic commit of documentation is enabled for a primary asset. It is part of the `PrimaryAssetDetailRead` and `PrimaryAssetUpdate` classes, allowing for both reading and updating this setting. The variable can be set to `None`, indicating that the setting is unspecified.
- **Use**: This variable is used to control and update the auto-commit behavior of documentation within the codebase for a primary asset.


---
### content 
- **Type**: `str | None`
- **Description**: The `content` variable is a string that can be set to `None`, representing the actual content associated with a node in the system. It is part of the `ContentRead` and `ContentCreate` classes, which are used to define the structure of content data in the application.
- **Use**: This variable is used to store and manage the textual content associated with a node, allowing for the creation and reading of content data.


---
### content_name 
- **Type**: `str | None`
- **Description**: The `content_name` variable is a field in the `DerivedContentUpdate` class, which is a Pydantic model used for updating derived content. It is an optional string that can be set to `None` if not provided.
- **Use**: This variable is used to specify or update the name of the content in the `DerivedContentUpdate` model.


---
### display_name 
- **Type**: `str`
- **Description**: The `display_name` variable is a string that represents the name displayed for a primary asset or version. It is used in various schemas such as `PrimaryAssetCreate`, `PrimaryAssetUpdate`, `VersionCreate`, and `VersionUpdate` to define or update the display name of these entities.
- **Use**: This variable is used to set or update the user-friendly name of primary assets and versions in the system.


---
### from_attributes 
- **Type**: `bool`
- **Description**: The `from_attributes` variable is a configuration option within the `Config` class of Pydantic models. When set to `True`, it allows the model to be initialized from a dictionary where keys are attribute names and values are the corresponding attribute values.
- **Use**: This variable is used to enable the initialization of Pydantic models from attribute-based dictionaries.


---
### misc_metadata 
- **Type**: `dict | None`
- **Description**: The `misc_metadata` variable is a dictionary that can store additional metadata related to content. It is defined as an optional field, meaning it can be `None` if no metadata is provided.
- **Use**: This variable is used to store supplementary metadata for content within the `ContentCreate` and `ContentRead` classes.


---
### relative_path 
- **Type**: `str`
- **Description**: The `relative_path` variable is a string that represents the path relative to a certain base directory or node. It is used within the `NodeCreate` and `NodeUpdate` classes to specify or update the path of a node in the system.
- **Use**: This variable is used to define or update the relative path of a node within the node creation and update processes.


# Classes

---
### Config 
- **Type**: `class`
- **Members**:
    - `from_attributes`: A class variable set to True, indicating configuration settings related to attribute handling.
- **Description**: The `Config` class is a simple configuration class with a single class variable `from_attributes` set to `True`. This class is used to define configuration settings that can be applied to other classes, particularly those that inherit from it or use it as a nested class. The `from_attributes` variable suggests that the configuration is related to handling attributes, possibly in the context of data models or schemas.


---
### ContentCreate 
- **Type**: `class`
- **Members**:
    - `node_id`: A UUID representing the unique identifier of the node.
    - `content_kind`: An instance of ContentKind indicating the type of content.
    - `content`: A string representing the content, which can be None.
    - `misc_metadata`: A dictionary for miscellaneous metadata, which can be None.
- **Description**: The ContentCreate class is a Pydantic model used for creating content entries, encapsulating essential attributes such as the node identifier, content type, and optional content and metadata. It ensures that the data conforms to the expected types and structures, facilitating the creation of content records in a structured and validated manner.
- **Inherits From**:
    - BaseModel


---
### ContentDetailRead 
- **Type**: `class`
- **Members**:
    - `node`: An instance of NodeDetailRead associated with the content.
- **Description**: The ContentDetailRead class is a detailed schema representation for content, extending the ContentRead class by including a node attribute of type NodeDetailRead. This class is part of a detailed read schema, providing more comprehensive information about content, particularly its association with a specific node, which includes versioning and creator details. The class configuration allows for attribute-based model creation, ensuring seamless integration with data sources.
- **Inherits From**:
    - ContentRead

**Nested Classes**
    - Config


---
### ContentRead 
- **Type**: `class`
- **Members**:
    - `id`: An optional UUID representing the unique identifier of the content.
    - `node_id`: An optional UUID representing the unique identifier of the associated node.
    - `content`: An optional string representing the actual content.
    - `content_kind`: A required ContentKind enum indicating the type of content.
    - `misc_metadata`: An optional dictionary containing miscellaneous metadata related to the content.
    - `created_at`: An optional datetime indicating when the content was created.
    - `updated_at`: An optional datetime indicating when the content was last updated.
- **Description**: The ContentRead class is a Pydantic model that represents a read-only view of content data, including its unique identifiers, type, and metadata. It is designed to be used in scenarios where content information needs to be retrieved and displayed, ensuring that all necessary attributes are available and correctly typed. The class also includes configuration to allow attribute-based access.
- **Inherits From**:
    - BaseModel

**Nested Classes**
    - Config


---
### DerivedContentUpdate 
- **Type**: `class`
- **Members**:
    - `content`: Optional string representing the content to be updated.
    - `content_name`: Optional string representing the name of the content to be updated.
- **Description**: The `DerivedContentUpdate` class is a simple data model used for updating content-related information, specifically the content itself and its name. It inherits from `BaseModel`, which is part of the Pydantic library, allowing for data validation and serialization. This class is likely used in scenarios where content updates are needed, providing a structured way to handle optional updates to both the content and its associated name.
- **Inherits From**:
    - BaseModel


---
### DocumentSourceCreate 
- **Type**: `class`
- **Members**:
    - `source_node_id`: A UUID representing the source node identifier.
    - `page_node_id`: A UUID representing the page node identifier.
- **Description**: The `DocumentSourceCreate` class is a Pydantic model used for creating a document source, containing identifiers for both the source node and the page node. It ensures that the data provided for these identifiers is valid and conforms to the UUID format.
- **Inherits From**:
    - BaseModel


---
### DocumentSourceDetailRead 
- **Type**: `class`
- **Members**:
    - `source_node`: An instance of NodeDetailRead representing the source node details.
- **Description**: The `DocumentSourceDetailRead` class is a detailed read schema that extends the `DocumentSourceRead` class by including additional information about the source node. It incorporates a `NodeDetailRead` instance to provide comprehensive details about the source node associated with a document source, enhancing the basic document source information with more in-depth node-related data.
- **Inherits From**:
    - DocumentSourceRead


---
### DocumentSourceRead 
- **Type**: `class`
- **Members**:
    - `page_node_id`: An optional UUID representing the page node identifier.
    - `source_node_id`: An optional UUID representing the source node identifier.
- **Description**: The `DocumentSourceRead` class is a Pydantic model that represents a read-only schema for document sources, containing optional UUID fields for both page and source node identifiers. It is configured to allow attribute-based initialization, making it suitable for data validation and serialization tasks in applications that manage document sources.
- **Inherits From**:
    - BaseModel

**Nested Classes**
    - Config


---
### ListWithCount 
- **Type**: `class`
- **Members**:
    - `results`: A list of items of type T.
    - `total_count`: An integer representing the total number of items.
- **Description**: The `ListWithCount` class is a generic container that extends `BaseModel` and is designed to hold a list of items along with a count of the total number of items. It is useful for scenarios where you need to return a collection of items and also provide metadata about the total number of items available, which can be particularly helpful in paginated data responses.
- **Inherits From**:
    - BaseModel
    - Generic[T]


---
### NodeCreate 
- **Type**: `class`
- **Members**:
    - `version_id`: A UUID representing the version identifier associated with the node.
    - `relative_path`: A string representing the relative path of the node.
- **Description**: The `NodeCreate` class is a schema definition for creating a new node, which is part of a versioned structure. It inherits from `BaseModel` and includes two fields: `version_id`, which is a UUID that links the node to a specific version, and `relative_path`, which specifies the node's location within the version's structure. This class is used to ensure that the necessary data is provided when a new node is being created in the system.
- **Inherits From**:
    - BaseModel


---
### NodeDetailRead 
- **Type**: `class`
- **Members**:
    - `version`: An instance of NodeVersionRead representing the version details of the node.
- **Description**: The NodeDetailRead class is a detailed schema representation of a node, inheriting from NodeRead, and includes additional version details through the nested NodeVersionRead class. This nested class extends VersionRead by adding a primary asset and an optional creator, providing a comprehensive view of a node's version and its associated metadata. The class is configured to populate its fields from attributes, ensuring seamless integration with data models.
- **Inherits From**:
    - NodeRead

**Nested Classes**
    - Config
    - NodeVersionRead


---
### NodeMetaRead 
- **Type**: `class`
- **Members**:
    - `id`: A universally unique identifier for the node.
    - `version_id`: A universally unique identifier for the version of the node.
    - `relative_path`: The relative path of the node.
    - `kind`: The kind of node, represented by the NodeKind enumeration.
    - `created_at`: The timestamp when the node was created, or None if not set.
    - `updated_at`: The timestamp when the node was last updated, or None if not set.
    - `misc_metadata`: A dictionary containing miscellaneous metadata about the node, or None if not set.
    - `total_files`: The total number of files associated with the node, or None if not set.
    - `depth`: The depth level of the node in a hierarchy.
- **Description**: The NodeMetaRead class extends the NodeRead class by adding additional metadata fields such as misc_metadata and total_files. It represents a node with its associated metadata, including identifiers, paths, kind, timestamps, and additional metadata that may be optional. This class is part of a schema used for reading node data, likely in a database or API context, and is configured to allow attribute-based initialization.
- **Inherits From**:
    - NodeRead

**Nested Classes**
    - Config


---
### NodeRead 
- **Type**: `class`
- **Members**:
    - `id`: A unique identifier for the node.
    - `version_id`: The identifier for the version associated with the node.
    - `relative_path`: The relative path of the node within its context.
    - `kind`: The type of node, represented by the NodeKind enum.
    - `created_at`: The timestamp when the node was created, or None if not set.
    - `updated_at`: The timestamp when the node was last updated, or None if not set.
    - `depth`: The depth level of the node in a hierarchy.
- **Description**: The NodeRead class is a Pydantic model that represents a node entity with attributes such as id, version_id, relative_path, kind, created_at, updated_at, and depth. It is used to encapsulate the data structure of a node, providing validation and serialization capabilities. The class is configured to allow attribute-based initialization, making it suitable for use in applications that require structured data handling.
- **Inherits From**:
    - BaseModel

**Nested Classes**
    - Config


---
### NodeUpdate 
- **Type**: `class`
- **Members**:
    - `relative_path`: An optional string representing the relative path of the node.
- **Description**: The `NodeUpdate` class is a simple data model used for updating node information, specifically the relative path of a node. It inherits from `BaseModel`, which is part of the Pydantic library, allowing for data validation and settings management. The class contains a single optional attribute, `relative_path`, which can be used to specify or update the path of a node within a larger structure.
- **Inherits From**:
    - BaseModel


---
### NodeVersionRead 
- **Type**: `class`
- **Members**:
    - `primary_asset`: Represents the primary asset associated with the node version.
    - `creator`: Represents the user who created the node version, or None if not applicable.
- **Description**: The `NodeVersionRead` class is a specialized version of the `VersionRead` class, designed to encapsulate additional details specific to a node version within a system. It includes information about the primary asset associated with the node version and optionally, the creator of the node version. This class is part of a broader schema for reading detailed information about nodes and their versions, facilitating the management and retrieval of version-specific data in a structured manner.
- **Inherits From**:
    - VersionRead


---
### PrimaryAssetCreate 
- **Type**: `class`
- **Members**:
    - `display_name`: A string representing the display name of the primary asset.
    - `kind`: An enumeration indicating the kind of primary asset.
- **Description**: The `PrimaryAssetCreate` class is a schema used for creating a new primary asset, encapsulating the essential attributes required for its creation. It inherits from `BaseModel`, which provides data validation and serialization capabilities. The class includes fields for the display name and the kind of the primary asset, ensuring that these attributes are specified when a new primary asset is created.
- **Inherits From**:
    - BaseModel


---
### PrimaryAssetDetailRead 
- **Type**: `class`
- **Members**:
    - `most_recent_version`: Holds the most recent version of the primary asset, if available.
    - `tags`: A list of tags associated with the primary asset.
    - `codebase_settings_auto_commit_docs`: Indicates if the codebase settings allow automatic commit of documents.
    - `browsable`: Determines if the primary asset is browsable based on its versions.
- **Description**: The `PrimaryAssetDetailRead` class extends `PrimaryAssetRead` to provide detailed information about a primary asset, including its most recent version, associated tags, and codebase settings. It includes a nested class `PrimaryAssetVersionRead` that extends `VersionRead` to include additional metadata about the root node and creator. The class also features a computed property `browsable` to determine if the asset is browsable based on its versions. This class is part of a schema for reading detailed information about primary assets in a system.
- **Inherits From**:
    - PrimaryAssetRead

**Methods**

---
#### PrimaryAssetDetailRead.browsable
The `browsable` function determines if a primary asset is browsable based on the browsability of its most recent version.
- **Inputs**:
    - None
- **Control Flow**:
    - Check if `self.most_recent_version` is not `None`.
    - If `self.most_recent_version` exists, return its `browsable` attribute.
    - If `self.most_recent_version` is `None`, return `False`.
- **Output**:
    - A boolean value indicating whether the primary asset is browsable.


**Nested Classes**
    - Config
    - PrimaryAssetVersionRead


---
### PrimaryAssetRead 
- **Type**: `class`
- **Members**:
    - `id`: A unique identifier for the primary asset.
    - `organization_id`: The identifier for the organization to which the asset belongs.
    - `kind`: The type of primary asset, defined by the PrimaryAssetKind enum.
    - `display_name`: The human-readable name of the primary asset.
    - `created_at`: The timestamp when the primary asset was created, or None if not set.
    - `updated_at`: The timestamp when the primary asset was last updated, or None if not set.
- **Description**: The `PrimaryAssetRead` class is a Pydantic model that represents a primary asset in a system, encapsulating essential information such as its unique identifier, organization association, type, display name, and timestamps for creation and last update. It is designed to facilitate the reading and validation of primary asset data, ensuring that the data adheres to the expected structure and types.
- **Inherits From**:
    - BaseModel

**Nested Classes**
    - Config


---
### PrimaryAssetTagCreate 
- **Type**: `class`
- **Members**:
    - `tag_id`: A UUID representing the unique identifier for the tag.
    - `primary_asset_id`: A UUID representing the unique identifier for the primary asset.
- **Description**: The `PrimaryAssetTagCreate` class is a schema used for creating a new association between a tag and a primary asset. It inherits from `BaseModel` and includes two UUID fields: `tag_id` and `primary_asset_id`, which uniquely identify the tag and the primary asset, respectively. This class is part of a larger system for managing assets and their metadata.
- **Inherits From**:
    - BaseModel


---
### PrimaryAssetTagDetailRead 
- **Type**: `class`
- **Members**:
    - `primary_asset`: An instance of PrimaryAssetRead representing the primary asset associated with the tag.
- **Description**: The `PrimaryAssetTagDetailRead` class is a detailed read schema that extends the `PrimaryAssetTagRead` class by including additional information about the primary asset associated with a tag. It provides a comprehensive view of the relationship between a primary asset and its tag by incorporating the `PrimaryAssetRead` instance, which contains detailed information about the primary asset itself.
- **Inherits From**:
    - PrimaryAssetTagRead


---
### PrimaryAssetTagRead 
- **Type**: `class`
- **Members**:
    - `tag_id`: A UUID representing the unique identifier of the tag.
    - `primary_asset_id`: A UUID representing the unique identifier of the primary asset.
- **Description**: The `PrimaryAssetTagRead` class is a simple data model that represents the association between a tag and a primary asset, using UUIDs to uniquely identify each. It inherits from `BaseModel`, which is part of the Pydantic library, allowing for data validation and serialization. The class is configured to allow attribute-based access to its fields.
- **Inherits From**:
    - BaseModel

**Nested Classes**
    - Config


---
### PrimaryAssetUpdate 
- **Type**: `class`
- **Members**:
    - `display_name`: Optional string representing the display name of the primary asset.
    - `codebase_settings_auto_commit_docs`: Optional boolean indicating if the codebase settings should automatically commit documents.
- **Description**: The `PrimaryAssetUpdate` class is a schema used for updating primary asset information, specifically allowing modifications to the display name and the auto-commit settings for codebase documents. It inherits from `BaseModel`, which provides validation and serialization capabilities.
- **Inherits From**:
    - BaseModel


---
### PrimaryAssetVersionRead 
- **Type**: `class`
- **Members**:
    - `root_node`: An optional NodeMetaRead instance representing the root node of the asset version.
    - `creator`: An optional UserRead instance representing the creator of the asset version.
- **Description**: The `PrimaryAssetVersionRead` class is a specialized version of the `VersionRead` class, designed to include additional metadata specific to primary asset versions. It includes optional attributes for the root node and the creator, providing a more detailed view of the asset version's structure and origin.
- **Inherits From**:
    - VersionRead


---
### TagCreate 
- **Type**: `class`
- **Members**:
    - `name`: A string representing the name of the tag.
    - `hex_color`: A string representing the hexadecimal color code of the tag.
    - `type`: A string representing the type of the tag.
- **Description**: The `TagCreate` class is a Pydantic model used to define the schema for creating a new tag. It includes fields for the tag's name, its hexadecimal color code, and its type, ensuring that these attributes are validated and structured according to the defined types when creating a tag instance.
- **Inherits From**:
    - BaseModel


---
### TagDetailRead 
- **Type**: `class`
- **Members**:
    - `primary_assets`: A list of PrimaryAssetRead objects associated with the tag.
- **Description**: The `TagDetailRead` class is a detailed schema representation of a tag, extending the `TagRead` class by including a list of primary assets associated with the tag. This class is part of a larger schema system used to represent detailed read views of various entities, and it provides additional context by linking tags to their related primary assets.
- **Inherits From**:
    - TagRead


---
### TagRead 
- **Type**: `class`
- **Members**:
    - `id`: A unique identifier for the tag.
    - `name`: The name of the tag.
    - `hex_color`: The hexadecimal color code associated with the tag.
    - `organization_id`: The identifier for the organization to which the tag belongs.
    - `type`: The type or category of the tag.
    - `created_at`: The timestamp when the tag was created, or None if not set.
    - `created_by`: The identifier of the user who created the tag.
    - `updated_at`: The timestamp when the tag was last updated, or None if not set.
    - `updated_by`: The identifier of the user who last updated the tag.
- **Description**: The `TagRead` class is a data model that represents a tag entity with attributes such as a unique identifier, name, color, organization association, type, and metadata about its creation and last update. It is used to encapsulate the details of a tag within the system, providing a structured way to manage and access tag information. The class inherits from `BaseModel`, which is part of the Pydantic library, allowing for data validation and serialization.
- **Inherits From**:
    - BaseModel

**Nested Classes**
    - Config


---
### UserRead 
- **Type**: `class`
- **Members**:
    - `id`: A string representing the unique identifier of the user.
    - `full_name`: A string representing the full name of the user.
    - `email`: A string representing the email address of the user.
- **Description**: The `UserRead` class is a Pydantic model that represents a user with basic attributes such as `id`, `full_name`, and `email`. It is used to define the structure of user data that can be read from a data source, ensuring that the data adheres to the specified types. The class also includes a configuration setting to allow attribute-based initialization.
- **Inherits From**:
    - BaseModel

**Nested Classes**
    - Config


---
### VersionCreate 
- **Type**: `class`
- **Members**:
    - `primary_asset_id`: A UUID representing the primary asset associated with the version.
    - `display_name`: A string representing the display name of the version.
- **Description**: The `VersionCreate` class is a Pydantic model used to define the schema for creating a new version of a primary asset. It includes fields for the primary asset's unique identifier and a display name, ensuring that any new version created adheres to this structure.
- **Inherits From**:
    - BaseModel


---
### VersionDetailRead 
- **Type**: `class`
- **Members**:
    - `primary_asset`: Holds the primary asset associated with the version.
    - `root_node`: Represents the root node of the version, if any.
    - `creator`: Stores the user who created the version, if available.
- **Description**: The `VersionDetailRead` class is a detailed schema representation of a version, extending the `VersionRead` class. It includes additional attributes such as the primary asset associated with the version, an optional root node, and an optional creator. This class is part of a larger schema system designed to handle detailed read operations for various entities, providing a comprehensive view of a version's details.
- **Inherits From**:
    - VersionRead

**Nested Classes**
    - Config


---
### VersionRead 
- **Type**: `class`
- **Members**:
    - `id`: A unique identifier for the version.
    - `primary_asset_id`: The unique identifier of the primary asset associated with this version.
    - `display_name`: The display name of the version.
    - `created_at`: The timestamp when the version was created, or None if not set.
    - `updated_at`: The timestamp when the version was last updated, or None if not set.
    - `status`: The status of the version, or None if not set.
    - `browsable`: A boolean indicating if the version is browsable.
- **Description**: The `VersionRead` class is a Pydantic model that represents a version of a primary asset, encapsulating details such as its unique identifier, associated primary asset ID, display name, creation and update timestamps, status, and whether it is browsable. It is configured to allow attribute-based initialization.
- **Inherits From**:
    - BaseModel

**Nested Classes**
    - Config


---
### VersionUpdate 
- **Type**: `class`
- **Members**:
    - `display_name`: An optional string representing the display name of the version update.
- **Description**: The `VersionUpdate` class is a simple data model used for updating version information, specifically allowing for the optional update of a version's display name. It inherits from `BaseModel`, which provides validation and serialization capabilities.
- **Inherits From**:
    - BaseModel


