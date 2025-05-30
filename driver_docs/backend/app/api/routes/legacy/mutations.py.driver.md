# Purpose
This Python file is a GraphQL API implementation using the Strawberry library, designed to handle various operations related to application notes, documents, and codebase uploads. The file defines several GraphQL types and inputs, such as `GenerateApplicationNoteOutput`, `UpdateApplicationNoteInput`, and `UploadCodebaseInput`, which are used to structure the data for mutations. The primary functionality revolves around creating, updating, and deleting application notes, as well as uploading source content and codebases. The file includes several mutation methods, such as `updateApplicationNote`, `deleteApplicationNote`, `uploadSourceContent`, and `uploadCodebase`, which perform these operations while ensuring access control and error handling.

The code integrates with a database to manage application notes and uses AWS S3 for handling file uploads, generating presigned URLs for secure file transfers. It employs access checks to ensure that users have the necessary permissions to perform operations on specific resources, leveraging functions like `check_access` and `get_derived_content_by_id`. The file is structured to be part of a larger application, likely serving as a backend component that interacts with a database and cloud storage, providing a public API for managing application notes and related content. The use of GraphQL allows for flexible and efficient data querying and manipulation, making this file a crucial part of a system that supports collaborative content management and storage.
# Imports and Dependencies

---
- `hashlib`
- `json`
- `os`
- `strawberry`
- `app.api.routes.legacy.orm_ops.check_access`
- `app.api.routes.legacy.orm_ops.get_derived_content_by_id`
- `app.api.routes.legacy.scalars.ID`
- `app.api.routes.legacy.scalars.JSON`
- `app.core.logger.logger`
- `app.utils.aws_s3.generate_put_presigned_url`
- `database.models_v1.DerivedContent`
- `database.models_v2.Node`
- `database.models_v2.PrimaryAsset`
- `database.models_v2.Version`
- `graphql.GraphQLError`
- `strawberry.types.Info`


# Global Variables

---
### content 
- **Type**: `str`
- **Description**: The `content` variable is a string that can be `None`, used as an input field in several input classes such as `UpdateApplicationNoteInput`, `UpdateDocumentInput`, and `WebhookInput`. It represents the content of a document or note that is being updated or processed.
- **Use**: This variable is used to store and update the content of application notes or documents in various mutation operations.


---
### editor_id 
- **Type**: `str | None`
- **Description**: The `editor_id` variable is a field within the `GenerateApplicationNoteInput` class, which is a Strawberry input type. It is an optional string that can be used to specify the identifier of an editor associated with generating an application note.
- **Use**: This variable is used to optionally provide an editor's identifier when generating an application note.


---
### errors 
- **Type**: `list`
- **Description**: The `errors` variable is a list that can contain strings or None values. It is used to store error messages or indicators of errors that may occur during the execution of a webhook operation.
- **Use**: This variable is used to capture and store error messages or statuses related to webhook operations, allowing for error handling and debugging.


---
### extra_context 
- **Type**: `JSON | None`
- **Description**: The `extra_context` variable is a field within the `WebhookInput` class, which is a Strawberry input type. It is defined as an optional JSON object, allowing for additional context to be provided when a webhook is triggered.
- **Use**: This variable is used to pass optional additional context data in JSON format when creating a webhook input.


---
### name 
- **Type**: `str | None`
- **Description**: The `name` variable is a string that can be set to `None` or a specific name value. It is used as an optional input field in several input classes, such as `UpdateApplicationNoteInput`, `UpdateDocumentInput`, and `WebhookInput`. This variable allows users to specify a name for the application note, document, or webhook content being processed.
- **Use**: This variable is used to store and pass the name of an application note, document, or webhook content within the input classes for various mutations.


---
### organization_id 
- **Type**: `str | None`
- **Description**: The `organization_id` variable is an optional string field within the `GenerateApplicationNoteInput` class, which is a Strawberry input type. It represents the unique identifier for an organization, allowing the system to associate the input data with a specific organization.
- **Use**: This variable is used to specify the organization context when generating an application note, enabling the system to handle the input data appropriately based on the organization.


# Classes

---
### ApplicationNoteEditInput 
- **Type**: `dataclass`
- **Members**:
    - `id`: Represents the unique identifier for the application note.
    - `prompt`: Stores the prompt text associated with the application note.
    - `workspace_id`: Indicates the workspace identifier where the application note is located.
- **Description**: The `ApplicationNoteEditInput` class is a data structure used to encapsulate the input data required for editing an application note. It includes fields for the note's unique identifier (`id`), the prompt text (`prompt`), and the workspace identifier (`workspace_id`). This class is likely used in a GraphQL API context to facilitate the mutation operations related to application notes.


---
### DeleteApplicationNoteOutput 
- **Type**: `class`
- **Members**:
    - `success`: Indicates whether the deletion of the application note was successful.
- **Description**: The `DeleteApplicationNoteOutput` class is a simple data structure used to represent the result of a delete operation for an application note. It contains a single boolean attribute, `success`, which indicates whether the deletion was successful or not. This class is part of a GraphQL API, as indicated by the `@strawberry.type` decorator, and is used to communicate the outcome of the delete operation back to the client.


---
### DocumentEditInput 
- **Type**: `dataclass`
- **Members**:
    - `document_id`: An identifier for the document.
    - `workspace_id`: An identifier for the workspace.
    - `codebase_id`: An identifier for the codebase.
    - `options`: A JSON object containing additional options.
- **Description**: The `DocumentEditInput` class is a data structure used to encapsulate the input parameters required for editing a document within a specific workspace and codebase. It includes identifiers for the document, workspace, and codebase, as well as a JSON object for additional options, facilitating the handling of document edit operations in a structured manner.


---
### GenerateApplicationNoteEditOutput 
- **Type**: `class`
- **Members**:
    - `call_id`: A string representing the unique identifier for the call.
    - `status`: A string indicating the status of the application note edit.
- **Description**: The `GenerateApplicationNoteEditOutput` class is a simple data structure used to represent the output of an application note edit operation. It contains two attributes: `call_id`, which uniquely identifies the call, and `status`, which indicates the current status of the edit operation. This class is likely used in a GraphQL API context, as suggested by the `@strawberry.type` decorator, to facilitate the transfer of data related to application note edits.


---
### GenerateApplicationNoteInput 
- **Type**: `dataclass`
- **Members**:
    - `codebase_id`: An identifier for the codebase.
    - `workspace_id`: An identifier for the workspace.
    - `prompt`: A string prompt for generating application notes.
    - `editor_id`: An optional identifier for the editor.
    - `organization_id`: An optional identifier for the organization.
- **Description**: The `GenerateApplicationNoteInput` class is a data structure used to encapsulate the input parameters required for generating an application note. It includes identifiers for the codebase and workspace, a prompt string, and optional identifiers for the editor and organization. This class is likely used in a context where application notes are generated based on these inputs, possibly in a system that integrates with a larger application or service.


---
### GenerateApplicationNoteOutput 
- **Type**: `class`
- **Members**:
    - `id`: A string identifier for the application note output.
- **Description**: The `GenerateApplicationNoteOutput` class is a simple data structure used to represent the output of generating an application note, containing only a single attribute, `id`, which serves as a unique identifier for the generated note. It is decorated with `@strawberry.type`, indicating its use in a GraphQL API context.


---
### Mutation 
- **Type**: `class`
- **Members**:
    - `updateApplicationNote`: A mutation method to update an application note with sanitized content and name.
    - `deleteApplicationNote`: A mutation method to delete an application note by its ID.
    - `UploadContentInput`: An input class for uploading content, containing codebase_id, workspace_id, and file_path.
    - `uploadSourceContent`: A mutation method to upload source content and generate a presigned URL for the upload.
    - `updateDocument`: A mutation method to update a document's content based on its ID.
    - `uploadCodebase`: A mutation method to upload a codebase and generate a presigned URL for the upload.
- **Description**: The `Mutation` class is a GraphQL mutation handler that provides several mutation methods for managing application notes, documents, and codebases. It includes methods for updating and deleting application notes, uploading source content, updating documents, and uploading codebases. Each mutation method performs access checks, handles exceptions, and logs errors. The class also defines an input class for uploading content, which specifies the necessary fields for the upload process.

**Methods**

---
#### Mutation.deleteApplicationNote
The `deleteApplicationNote` function deletes an application note from the database after verifying user access and the note's existence.
- **Inputs**:
    - `info`: An instance of `Info` that provides context, including the session and user information.
    - `id`: An optional `ID` representing the unique identifier of the application note to be deleted.
- **Control Flow**:
    - Retrieve the session and user from the `info` context.
    - Check if the user has access to delete the note using `check_access`; if not, raise a `GraphQLError` with a 'FORBIDDEN' code.
    - Attempt to retrieve the application note by its ID using `get_derived_content_by_id`.
    - If the note does not exist, raise a `GraphQLError` with a 'BAD_REQUEST' code indicating the note was not found.
    - If the note exists, delete it from the session and commit the transaction.
    - If any exception occurs during the process, log the error and raise a `GraphQLError` with a 'BAD_REQUEST' code indicating the note was not deleted.
- **Output**:
    - The function returns `None` after successfully deleting the application note or raises a `GraphQLError` if an error occurs.


---
#### Mutation.updateApplicationNote
The `updateApplicationNote` function updates an application note's name and content in the database after verifying user access and sanitizing input data.
- **Inputs**:
    - `info`: An instance of `Info` that provides context, including the session and user information.
    - `input`: An instance of `UpdateApplicationNoteInput` containing the ID of the note to update, and optionally the new name and content for the note.
- **Control Flow**:
    - Retrieve the session and user from the `info` context.
    - Check if the user has access to the application note using `check_access`; if not, raise a `GraphQLError` with a 'FORBIDDEN' code.
    - Attempt to retrieve the application note by its ID using `get_derived_content_by_id`; if not found, raise a `GraphQLError` with a 'BAD_REQUEST' code.
    - Define a helper function `escape_html` to sanitize HTML content by replacing special characters with their HTML-safe equivalents.
    - Sanitize the input name and content using `escape_html` if they are provided.
    - Parse the existing note content from JSON, update it with the sanitized name and content if they are provided, and convert it back to JSON.
    - Add the updated note to the session and commit the transaction to save changes.
    - If any exception occurs, rollback the session, log the error, and raise a `GraphQLError` with a 'BAD_REQUEST' code.
- **Output**:
    - The function does not return any value; it raises a `GraphQLError` if an error occurs during the update process.


---
#### Mutation.updateDocument
The `updateDocument` function updates the content of a document in the database if it belongs to the user's organization, handling errors and rolling back transactions if necessary.
- **Inputs**:
    - `info`: An instance of `Info` that provides context, including the database session and the user making the request.
    - `input`: An instance of `UpdateDocumentInput` containing the ID of the document to update and the new content.
- **Control Flow**:
    - Retrieve the database session and user from the `info` context.
    - Attempt to query the `DerivedContent` table to find a document with the specified ID that belongs to the user's organization.
    - If the document is not found, raise a `GraphQLError` indicating the document was not found.
    - If the document is found, update its content with the new content provided in the `input`.
    - Add the updated document to the session and commit the transaction to save changes.
    - If any exception occurs during the process, roll back the session to undo any changes and log the error.
    - Raise a `GraphQLError` if an exception occurs, indicating the update failed.
- **Output**:
    - The function does not return any value (returns `None`).


---
#### Mutation.uploadCodebase
The `uploadCodebase` function generates a presigned URL for uploading a codebase file to an S3 bucket, ensuring necessary validations and logging.
- **Inputs**:
    - `info`: An instance of `Info` that provides context, including the user making the request.
    - `input`: An instance of `UploadCodebaseInput` containing the `workspace_id` and `file_path` for the codebase to be uploaded.
- **Control Flow**:
    - Extracts user and organization details from the `info` context and input parameters.
    - Logs the initiation of the codebase upload process with relevant identifiers.
    - Checks for the presence of essential parameters (`codebase_name`, `file_path`, `org_id`, `workspace_id`, `creator_id`) and raises a `GraphQLError` if any are missing.
    - Attempts to generate a unique upload key using a hash of the organization ID and the file name.
    - Logs the generated upload key for tracking purposes.
    - Creates metadata for the codebase upload, including organization and workspace details.
    - Generates a presigned URL for uploading the codebase file to an S3 bucket using the `generate_put_presigned_url` function.
    - Returns the generated presigned URL for the client to use for uploading the file.
    - Catches and logs any exceptions that occur during the URL generation process, raising a `GraphQLError` if an error occurs.
- **Output**:
    - A presigned URL string for uploading the codebase file to an S3 bucket.


---
#### Mutation.uploadSourceContent
The `uploadSourceContent` function generates a presigned URL for uploading a supplemental document to an AWS S3 bucket, ensuring access permissions and input validity.
- **Inputs**:
    - `info`: An `Info` object containing context information such as the user and session.
    - `input`: An `UploadContentInput` object containing `workspace_id`, `codebase_id`, and `file_path`.
- **Control Flow**:
    - Extracts `workspace_id`, `codebase_id`, and `file_path` from the `input` parameter.
    - Retrieves the user and session from the `info` context.
    - Logs the upload attempt with organization, workspace, and user details.
    - Checks if any of `codebase_id`, `file_path`, `workspace_id`, or `creator_id` are missing and raises a `GraphQLError` if so.
    - Verifies access to the codebase using `check_access` and raises a `GraphQLError` if access is denied.
    - Attempts to generate a presigned URL for uploading the document to S3.
    - Calculates a hash of the organization ID to use in the S3 key and metadata.
    - Generates the S3 upload key and metadata for the document.
    - Calls `generate_put_presigned_url` to create the upload URL.
    - Logs the successful generation of the upload URL and returns it.
    - Catches any exceptions during URL generation, logs the error, and raises a `GraphQLError`.
- **Output**:
    - A string representing the presigned URL for uploading the document to S3.


**Nested Classes**
    - UploadContentInput


---
### UpdateApplicationNoteInput 
- **Type**: `dataclass`
- **Members**:
    - `id`: The unique identifier for the application note.
    - `content`: The content of the application note, which can be None.
    - `name`: The name of the application note, which can be None.
- **Description**: The `UpdateApplicationNoteInput` class is a data structure used to encapsulate the input data required for updating an application note. It includes an identifier for the note, and optionally, the content and name of the note. This class is used in the context of GraphQL mutations to facilitate the update operation on application notes.


---
### UpdateApplicationNoteOutput 
- **Type**: `class`
- **Members**:
    - `success`: Indicates whether the update operation was successful.
- **Description**: The `UpdateApplicationNoteOutput` class is a simple data structure used to represent the result of an update operation on an application note, specifically indicating whether the operation was successful through a boolean attribute.


---
### UpdateDocumentInput 
- **Type**: `dataclass`
- **Members**:
    - `id`: The unique identifier for the document.
    - `content`: The content of the document, which can be None.
    - `name`: The name of the document, which can be None.
- **Description**: The `UpdateDocumentInput` class is a data structure used to encapsulate the input data required for updating a document. It includes an identifier for the document, and optionally, the content and name of the document. This class is used in the context of GraphQL mutations to facilitate document updates.


---
### UploadCodebaseInput 
- **Type**: `class`
- **Members**:
    - `workspace_id`: A string representing the ID of the workspace.
    - `file_path`: A string representing the file path to be uploaded.
- **Description**: The `UploadCodebaseInput` class is a simple data structure used to encapsulate the input parameters required for uploading a codebase. It contains two attributes: `workspace_id`, which identifies the workspace where the codebase is to be uploaded, and `file_path`, which specifies the path of the file to be uploaded. This class is used as an input type in GraphQL mutations to facilitate the upload process.


---
### UploadContentInput 
- **Type**: `class`
- **Members**:
    - `codebase_id`: A string representing the unique identifier for the codebase.
    - `workspace_id`: A string representing the unique identifier for the workspace.
    - `file_path`: A string representing the file path of the content to be uploaded.
- **Description**: The `UploadContentInput` class is a simple data structure used to encapsulate the input parameters required for uploading content. It includes identifiers for the codebase and workspace, as well as the file path of the content to be uploaded. This class is used in the context of a GraphQL mutation to facilitate the upload process by providing necessary metadata.


---
### UploadSourceContentOutput 
- **Type**: `class`
- **Members**:
    - `upload_url`: A string representing the URL to which content can be uploaded.
- **Description**: The `UploadSourceContentOutput` class is a simple data structure used to encapsulate the URL generated for uploading source content. It is defined as a Strawberry GraphQL type, which means it is intended to be used as part of a GraphQL API response, specifically to provide clients with a URL where they can upload content.


---
### WebhookInput 
- **Type**: `dataclass`
- **Members**:
    - `content`: Optional string representing the content of the webhook.
    - `document_id`: An ID representing the document associated with the webhook.
    - `errors`: Optional list of strings representing any errors related to the webhook.
    - `extra_context`: Optional JSON object providing additional context for the webhook.
    - `name`: Optional string representing the name associated with the webhook.
    - `prompt`: A string representing the prompt for the webhook.
- **Description**: The `WebhookInput` class is a data structure used to encapsulate input data for a webhook operation. It includes fields for content, document identification, potential errors, additional context, a name, and a prompt. This class is designed to be used as an input type in a GraphQL API, specifically for operations that involve processing or handling webhook data.


---
### WebhookOutput 
- **Type**: `class`
- **Members**:
    - `document_id`: A string representing the document ID associated with the webhook output.
- **Description**: The `WebhookOutput` class is a simple data structure used to represent the output of a webhook operation, specifically containing a single attribute, `document_id`, which holds the identifier of the document involved in the webhook process. This class is defined as a Strawberry GraphQL type, indicating its use in a GraphQL API context.


# Functions

---
### escape_html 
The `escape_html` function replaces special HTML characters in a string with their corresponding HTML entity codes to prevent HTML injection.
- **Inputs**:
    - `obj`: A string that potentially contains HTML special characters that need to be escaped.
- **Control Flow**:
    - The function takes a string input `obj`.
    - It sequentially replaces occurrences of '&', '<', '>', '"', and "'" in the string with their respective HTML entity codes: '&amp;', '&lt;', '&gt;', '&quot;', and '&#039;'.
    - The function returns the modified string with all replacements made.
- **Output**:
    - A string with HTML special characters replaced by their corresponding HTML entity codes.


