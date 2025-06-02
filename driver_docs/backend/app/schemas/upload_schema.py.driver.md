# Purpose
This code defines a narrow functionality related to handling file uploads, using Pydantic models to enforce data validation and structure. It consists of two classes, `UploadRequest` and `UploadResponse`, both inheriting from `BaseModel`, which is part of the Pydantic library. The `UploadRequest` class includes a field `file_path` and a custom validator `must_be_zip_or_pdf` to ensure that the file path ends with either ".zip" or ".pdf", raising a `ValueError` if it does not. The `UploadResponse` class defines fields for `upload_url`, `primary_asset_id`, and `version_id`, with the latter two being UUIDs, indicating that they are unique identifiers. This code is a concise example of using Pydantic for data validation and serialization in a file upload context.
# Imports and Dependencies

---
- `typing`
- `uuid`
- `pydantic`


# Classes

---
### UploadRequest 
- **Type**: `class`
- **Members**:
    - `file_path`: A string representing the path of the file to be uploaded.
- **Description**: The `UploadRequest` class is a Pydantic model that represents a request to upload a file, ensuring that the file path provided ends with either a ".zip" or ".pdf" extension. It includes a field validator to enforce this constraint, raising a `ValueError` if the condition is not met.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### UploadRequest.must_be_zip_or_pdf
The function `must_be_zip_or_pdf` validates that a given file path ends with either '.zip' or '.pdf'.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods to refer to the class itself.
    - `v`: The file path to be validated, expected to be a string.
- **Control Flow**:
    - The function checks if the file path `v` does not end with '.zip' or '.pdf' using the `lower()` method to ensure case insensitivity.
    - If the file path does not meet the criteria, a `ValueError` is raised with a specific error message.
    - If the file path is valid, it is returned unchanged.
- **Output**:
    - The function returns the validated file path if it ends with '.zip' or '.pdf'; otherwise, it raises a `ValueError`.



---
### UploadResponse 
- **Type**: `class`
- **Members**:
    - `upload_url`: A string representing the URL where the file can be uploaded.
    - `primary_asset_id`: A UUID representing the primary asset identifier.
    - `version_id`: A UUID representing the version identifier of the asset.
- **Description**: The `UploadResponse` class is a Pydantic model that encapsulates the response details for an upload operation, including the URL for uploading, the primary asset ID, and the version ID. It inherits from `BaseModel`, which provides data validation and serialization capabilities.
- **Inherits From**:
    - BaseModel


