# Purpose
The provided Python code defines a `ContentService` class, which is part of a larger application likely dealing with content management. This class is designed to interact with a database to perform operations related to content retrieval, filtering, sorting, and metadata management. It uses SQLAlchemy and SQLModel for database interactions, and FastAPI for handling HTTP exceptions. The class provides methods to list content, retrieve content by ID, generate download URLs for content stored in AWS S3, and fetch tags associated with content. It also includes a utility function to convert markdown content to reStructuredText using the `pypandoc` library.

The `ContentService` class is a cohesive unit that encapsulates functionality related to content management, making it a critical component of a content management system. It leverages several external modules and libraries, such as `botocore` for AWS interactions and `sqlalchemy` for database operations, indicating its integration into a broader system architecture. The class is structured to handle various content-related operations efficiently, with methods that ensure data integrity and provide detailed logging for traceability. Additionally, the code includes error handling to manage exceptions and provide meaningful HTTP responses, enhancing the robustness of the service.
# Imports and Dependencies

---
- `hashlib`
- `uuid.UUID`
- `pypandoc`
- `botocore.exceptions.ClientError`
- `database.models_v1.DerivedContent`
- `database.models_v1.DocumentSource`
- `database.models_v1.Enum_Derived_Content_Status`
- `database.models_v1.Tag`
- `database.models_v2.Node`
- `database.models_v2.PrimaryAsset`
- `database.models_v2.PrimaryAssetTag`
- `database.models_v2.Version`
- `fastapi.HTTPException`
- `fastapi.status`
- `sqlalchemy.orm.selectinload`
- `sqlalchemy.sql.selectable.Select`
- `sqlmodel.Session`
- `sqlmodel.asc`
- `sqlmodel.desc`
- `sqlmodel.func`
- `sqlmodel.or_`
- `sqlmodel.select`
- `sqlmodel.text`
- `app.core.logger.logger`
- `app.repositories.base_repository.BaseRepository`
- `app.schemas.content_schema.ContentTagsResponse`
- `app.schemas.content_schema.DownloadContentResponse`
- `app.schemas.content_schema.ListContentInput`
- `app.schemas.content_schema.ListContentResult`
- `app.schemas.content_schema.ListContentResults`
- `app.schemas.content_schema.TagResult`
- `app.utils.aws_s3.generate_org_get_presigned_url`
- `app.utils.aws_s3.head_org_object`


# Classes

---
### ContentService 
- **Type**: `class`
- **Members**:
    - `session`: Holds the database session for executing queries.
    - `content_repository`: Manages database operations for DerivedContent entities.
    - `document_source_repository`: Manages database operations for DocumentSource entities.
    - `node_repository`: Manages database operations for Node entities.
- **Description**: The ContentService class provides a comprehensive suite of methods for managing and retrieving content-related data from a database. It utilizes SQL queries to fetch, filter, and sort content based on various criteria such as organization ID, content type, and tags. The class also includes functionality to convert markdown content to reStructuredText, retrieve content by ID, generate download URLs for content stored in S3, and fetch content tags. It leverages a session object for database interactions and employs repositories for specific entity operations, ensuring efficient data handling and retrieval.

**Methods**

---
#### ContentService.__init__
The `__init__` function initializes a `ContentService` object with a database session and sets up repositories for content, document sources, and nodes.
- **Inputs**:
    - `self`: An instance of the ContentService class being initialized.
    - `session`: A SQLAlchemy Session object used for database operations.
- **Control Flow**:
    - Assigns the provided session to the instance variable `self.session`.
    - Initializes `self.content_repository` with a `BaseRepository` for `DerivedContent` using the session.
    - Initializes `self.document_source_repository` with a `BaseRepository` for `DocumentSource` using the session.
    - Initializes `self.node_repository` with a `BaseRepository` for `Node` using the session.
- **Output**:
    - The function does not return any value; it initializes the instance variables.


---
#### ContentService._apply_filters
The `_apply_filters` function applies various filters to a SQLAlchemy Select statement based on the criteria provided in a `ListContentInput` object.
- **Inputs**:
    - `self`: An instance of the `ContentService` class.
    - `statement`: A SQLAlchemy `Select` object representing the initial query to which filters will be applied.
    - `search_input`: An instance of `ListContentInput` containing the filtering criteria such as text, order, status, version_id, content_type_name, tags, and tag_ids.
- **Control Flow**:
    - Check if `search_input.text` is provided, and if so, add filters to the statement for `Node.relative_path` and `PrimaryAsset.display_name` containing the text.
    - Check if `search_input.order` is provided, and if so, add a filter to the statement for `DerivedContent.order`.
    - Check if `search_input.status` is provided, validate it against `Enum_Derived_Content_Status`, and add a filter for `Version.status` if valid, otherwise raise an HTTPException.
    - Check if `search_input.version_id` is provided, and if so, add a filter for `Version.id`.
    - Check if `search_input.content_type_name` is provided, log the filtering action, and add a filter for `DerivedContent.content_kind`.
    - Check if `search_input.tags` or `search_input.tag_ids` are provided, join `PrimaryAssetTag` and `Tag` tables, and add filters for `Tag.name` and `Tag.id` respectively.
- **Output**:
    - A modified SQLAlchemy `Select` object with the applied filters based on the provided `ListContentInput`.


---
#### ContentService._apply_sorting
The `_apply_sorting` function applies sorting to a SQLAlchemy Select statement based on user-specified criteria.
- **Inputs**:
    - `self`: An instance of the `ContentService` class, which contains the content repository and other related repositories.
    - `statement`: A SQLAlchemy `Select` object representing the SQL query to which sorting will be applied.
    - `search_input`: An instance of `ListContentInput` containing user-specified sorting criteria, including `sort_by` and `sort_direction`.
- **Control Flow**:
    - Check if `search_input.sort_by` is provided; if not, return the original statement without modification.
    - Verify that the `sort_by` attribute exists in the content repository model; if not, raise a `ValueError`.
    - Construct the field name for sorting using the model's table name and the `sort_by` attribute.
    - Determine the sorting direction based on `search_input.sort_direction`; apply ascending or descending order accordingly using `asc` or `desc` functions.
    - If the `sort_direction` is invalid, raise a `ValueError`.
    - Return the modified `Select` statement with the applied sorting.
- **Output**:
    - A SQLAlchemy `Select` object with sorting applied based on the specified criteria.


---
#### ContentService._build_base_query
The `_build_base_query` function constructs a foundational SQL query to retrieve content-related data filtered by organization ID from multiple database tables.
- **Inputs**:
    - `self`: An instance of the `ContentService` class, which provides context for the method.
    - `organization_id`: A string representing the organization ID used to filter the query results.
- **Control Flow**:
    - The function begins by constructing a SQL `select` statement targeting the `DerivedContent` table.
    - It performs a series of `join` operations to link the `Node`, `Version`, and `PrimaryAsset` tables, establishing relationships between these tables based on their respective keys.
    - A `where` clause is applied to filter the results, ensuring that only entries with a matching `organization_id` in the `PrimaryAsset` table are included.
    - The constructed query is returned as a `Select` object, which can be further processed or executed.
- **Output**:
    - The function returns a `Select` object representing the constructed SQL query.


---
#### ContentService._get_list_content
The `_get_list_content` function retrieves a list of `DerivedContent` objects and their total count from the database based on specified filters, sorting, and pagination for a given organization.
- **Inputs**:
    - `self`: An instance of the `ContentService` class, which provides access to the session and repository methods.
    - `organization_id`: A string representing the unique identifier of the organization for which the content is being retrieved.
    - `search_input`: An instance of `ListContentInput` containing search parameters such as filters, sorting options, and pagination details.
- **Control Flow**:
    - The function begins by building a base query using the `_build_base_query` method, which selects `DerivedContent` entries associated with the given `organization_id`.
    - It applies filters to the query using the `_apply_filters` method based on the criteria specified in `search_input`.
    - The total count of entries matching the query is calculated using a subquery and the `func.count()` function.
    - The query is then sorted according to the criteria specified in `search_input` using the `_apply_sorting` method.
    - The query is configured to pre-fetch related `DerivedContent.node` entities using `selectinload` to optimize attribute access.
    - The final query is executed with pagination (offset and limit) to retrieve the results.
    - The function returns a tuple containing the list of `DerivedContent` objects and the total count of matching entries.
- **Output**:
    - A tuple consisting of a list of `DerivedContent` objects and an integer representing the total count of entries matching the query.


---
#### ContentService.convert_markdown_to_rst
The `convert_markdown_to_rst` function converts a given markdown string to reStructuredText (rst) format using the pypandoc library.
- **Inputs**:
    - `content`: A string containing markdown content that needs to be converted to reStructuredText format.
- **Control Flow**:
    - Logs an informational message indicating the start of the conversion process.
    - Attempts to convert the markdown content to rst using the `pypandoc.convert_text` function.
    - If the conversion is successful, returns the converted rst content.
    - If a `RuntimeError` occurs during conversion, raises an `HTTPException` with a 500 status code and a 'Conversion error' detail.
- **Output**:
    - The function returns a string containing the converted reStructuredText content.


---
#### ContentService.get_content_by_id
The `get_content_by_id` function retrieves a specific content item by its ID and verifies its association with a given organization.
- **Inputs**:
    - `content_id`: A UUID representing the unique identifier of the content to be retrieved.
    - `organization_id`: A string representing the unique identifier of the organization to which the content should belong.
- **Control Flow**:
    - Logs an informational message indicating the start of the content retrieval process by ID.
    - Attempts to retrieve the content from the content repository using the provided `content_id`.
    - Checks if the retrieved content is `None` or if its associated organization ID does not match the provided `organization_id`.
    - If the content is not found or the organization ID does not match, logs an error message and raises an `HTTPException` with a 404 status code indicating that the content was not found.
    - If the content is found and the organization ID matches, returns the content.
- **Output**:
    - Returns a `DerivedContent` object if the content is found and belongs to the specified organization; otherwise, raises an `HTTPException` with a 404 status code.


---
#### ContentService.get_content_download_url
The function `get_content_download_url` retrieves a presigned URL for downloading content from S3 based on a given node ID and organization ID.
- **Inputs**:
    - `node_id`: A UUID representing the unique identifier of the content node to be downloaded.
    - `organization_id`: A string representing the unique identifier of the organization to which the content belongs.
- **Control Flow**:
    - Log the attempt to fetch content by the given node ID.
    - Retrieve the node from the repository using the node ID and organization ID as conditions.
    - Check if the node exists and if its organization ID matches the provided organization ID.
    - If the node is not found or the organization ID does not match, log an error and raise an HTTP 404 exception.
    - Construct a download key using the primary asset ID, version ID, and relative path of the node.
    - Log the constructed download key.
    - Attempt to check if the object exists in the S3 bucket using the `head_org_object` function.
    - If the object exists, generate a presigned URL using `generate_org_get_presigned_url` and return a `DownloadContentResponse` with the URL, content name, and status.
    - If a `ClientError` occurs, log the exception and raise an HTTP 404 exception.
- **Output**:
    - Returns a `DownloadContentResponse` object containing the presigned download URL, content name, and status if successful; otherwise, raises an HTTP 404 exception if the content is not found or not downloadable.


---
#### ContentService.get_content_tags
The `get_content_tags` function retrieves and returns the tags associated with a specific content item for a given organization.
- **Inputs**:
    - `content_id`: A UUID representing the unique identifier of the content for which tags are being fetched.
    - `organization_id`: A string representing the unique identifier of the organization to which the content belongs.
- **Control Flow**:
    - Logs the start of the tag fetching process for the specified content ID.
    - Executes a database query to retrieve the primary asset associated with the given content ID and organization ID, including its tags.
    - Checks if the primary asset is found; if not, logs an error and raises an HTTP 404 exception indicating the primary asset is not found.
    - If the primary asset is found, iterates over its tags to create a list of `TagResult` objects, each containing tag details such as ID, name, color, and timestamps.
    - Logs the successful retrieval of tags for the specified content ID.
    - Returns a `ContentTagsResponse` object containing the list of `TagResult` objects.
- **Output**:
    - A `ContentTagsResponse` object containing a list of `TagResult` objects, each representing a tag associated with the specified content.


---
#### ContentService.get_list_content
The `get_list_content` function retrieves a list of content for a specified organization based on search criteria and returns the results in a structured format.
- **Inputs**:
    - `self`: An instance of the `ContentService` class.
    - `organization_id`: A string representing the unique identifier of the organization for which content is being retrieved.
    - `search_input`: An instance of `ListContentInput` containing search criteria such as offset, limit, sort options, and filters.
- **Control Flow**:
    - Logs the start of the content retrieval process for the specified organization and search input.
    - Attempts to retrieve content and total count using the `_get_list_content` method, handling any `ValueError` exceptions by logging the error and raising an HTTP 400 error.
    - Initializes an empty list `content_results` to store the formatted content results.
    - Iterates over the retrieved content results, creating `ListContentResult` objects for each and appending them to `content_results`.
    - Logs the successful retrieval of content for the organization.
    - Returns a `ListContentResults` object containing the list of content results, along with pagination information and total count.
- **Output**:
    - Returns a `ListContentResults` object containing the list of content results, pagination details (offset and limit), and the total count of content items.



# Functions

---
### organization_bucket_from_organization_id 
The function generates a unique bucket name for an organization by hashing its ID.
- **Inputs**:
    - `organization_id`: A string representing the unique identifier of the organization.
- **Control Flow**:
    - The function encodes the organization_id into bytes.
    - It then computes the SHA-256 hash of the encoded organization_id.
    - The resulting hash is converted to a hexadecimal string.
    - The function returns the first 63 characters of this hexadecimal string.
- **Output**:
    - A string representing the first 63 characters of the SHA-256 hash of the organization_id, which serves as a unique bucket name.


