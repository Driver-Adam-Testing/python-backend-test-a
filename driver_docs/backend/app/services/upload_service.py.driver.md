# Purpose
The provided Python code defines an `UploadService` class, which is part of a larger application, likely a web service, that handles file uploads. This class is designed to create a new asset version and generate a pre-signed URL for uploading files to an AWS S3 bucket. The service supports files with `.zip` and `.pdf` extensions, categorizing them as codebases or regular files, respectively. The class uses SQLAlchemy for database interactions, specifically to create and store new `PrimaryAsset` and `Version` records, which are essential components of the application's data model. The code also includes error handling for duplicate asset names and logs relevant information for debugging and auditing purposes.

The `create_asset_version_and_upload_url` method is the core functionality of this class, taking a `UserToken` and an `UploadRequest` as inputs. It processes the file name, determines the asset kind, and constructs a unique upload key for S3 storage. The method also generates metadata for the asset and uses a utility function to create a pre-signed URL, which is returned in an `UploadResponse`. This setup indicates that the code is part of a backend service, likely using FastAPI for handling HTTP requests, and is designed to be integrated into a larger system that manages digital assets. The code is structured to be reusable and maintainable, with clear separation of concerns between database operations, file handling, and external service interactions.
# Imports and Dependencies

---
- `hashlib`
- `os`
- `re`
- `urllib.parse.unquote_plus`
- `database.models_v2.PrimaryAsset`
- `database.models_v2.Version`
- `database.models_v2_enums.PrimaryAssetKind`
- `database.models_v2_enums.VersionStatus`
- `fastapi.HTTPException`
- `sqlalchemy.exc.IntegrityError`
- `app.api.auth.UserToken`
- `app.api.session.CurrentSession`
- `app.core.logger.logger`
- `app.schemas.upload_schema.UploadRequest`
- `app.schemas.upload_schema.UploadResponse`
- `app.utils.aws_s3.generate_put_presigned_url`


# Classes

---
### UploadService 
- **Type**: `class`
- **Members**:
    - `session`: Holds the current session for database operations.
- **Description**: The `UploadService` class is responsible for handling the creation of asset versions and generating upload URLs for files. It supports files with .zip and .pdf extensions, creating a new asset and version in the database, and generating a presigned URL for uploading the file to an S3 bucket. The class ensures that the asset name is unique and handles potential integrity errors during the asset creation process.

**Methods**

---
#### UploadService.__init__
The `__init__` function initializes an instance of the `UploadService` class with a given database session.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the database session to be used by the `UploadService` instance.
- **Control Flow**:
    - The function assigns the provided `session` to the instance variable `self.session`.
- **Output**:
    - The function does not return any value (returns `None`).


---
#### UploadService.create_asset_version_and_upload_url
The function creates a new asset version and generates a presigned URL for uploading a file to an S3 bucket.
- **Inputs**:
    - `user`: A UserToken object containing information about the user, including their organization ID and name.
    - `request`: An UploadRequest object containing the file path of the file to be uploaded.
- **Control Flow**:
    - Extract the file name from the request's file path and determine its type (zip or pdf).
    - Set asset properties based on the file type, including asset name, kind, content type, and codebase settings.
    - Sanitize the file name by replacing non-alphanumeric characters and spaces with underscores.
    - Hash the organization ID to create a unique identifier for the upload key.
    - Begin a database session to create a new PrimaryAsset and Version entry in the database.
    - Generate a relative path and upload key for the asset using the asset and version IDs.
    - Create asset metadata and generate a presigned URL for uploading the file to an S3 bucket.
    - Handle IntegrityError exceptions by logging an error and raising an HTTPException if an asset with the same name already exists.
    - Log the successful generation of the upload URL and return an UploadResponse with the upload URL, primary asset ID, and version ID.
- **Output**:
    - An UploadResponse object containing the generated upload URL, primary asset ID, and version ID.



