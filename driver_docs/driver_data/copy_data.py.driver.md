# Purpose
This Python script is designed to facilitate the migration of codebase data and associated content from a source environment to a destination environment. It achieves this by copying database records and synchronizing files stored in Amazon S3 buckets. The script is structured as a command-line tool, utilizing the `argparse` module to accept parameters such as organization ID, codebase ID, and flags to skip database or S3 operations. The core functionality is encapsulated in several functions that handle different aspects of the migration process, including generating content type mappings, updating content types, copying codebase and derived content, and managing chunks and embeddings. The script also includes a function to synchronize S3 objects to a MinIO instance, addressing potential cross-account permission issues.

The script is intended to be executed as a standalone script, as indicated by the `if __name__ == "__main__":` block, which loads environment variables and parses command-line arguments before invoking the `main` function. The `main` function orchestrates the migration process by establishing database connections, managing sessions, and invoking the appropriate functions to perform the data transfer. The script relies on several external libraries, including `boto3` for AWS interactions, `sqlmodel` for database operations, and `dotenv` for environment variable management. The script is designed to handle errors gracefully, with rollback mechanisms in place to ensure data integrity in case of failures during the migration process.
# Imports and Dependencies

---
- `argparse`
- `hashlib`
- `os`
- `shutil`
- `time`
- `uuid`
- `boto3`
- `database.models_v1`
- `dotenv`
- `sqlmodel`


# Global Variables

---
### args 
- **Type**: `argparse.Namespace`
- **Description**: The `args` variable is an instance of `argparse.Namespace` that holds the command-line arguments parsed by the `argparse.ArgumentParser`. It contains the values for `org-id`, `codebase-id`, `skip-db`, and `skip-s3` as specified by the user when running the script.
- **Use**: This variable is used to pass the parsed command-line arguments to the `main` function, which then uses these values to control the execution flow of the script.


---
### parser 
- **Type**: `argparse.ArgumentParser`
- **Description**: The `parser` variable is an instance of `argparse.ArgumentParser`, which is used to handle command-line arguments for the script. It is configured to accept arguments for organization ID, codebase ID, and optional flags to skip database and S3 operations.
- **Use**: This variable is used to parse and manage command-line arguments provided to the script, enabling the user to specify parameters for data migration operations.


# Functions

---
### copy_chunks_and_embeddings 
The function `copy_chunks_and_embeddings` copies chunks and their embeddings from a source database session to a destination session for specified derived content IDs.
- **Inputs**:
    - `source_session`: A SQLAlchemy Session object connected to the source database from which chunks and embeddings will be copied.
    - `destination_session`: A SQLAlchemy Session object connected to the destination database where chunks and embeddings will be copied to.
    - `derived_content_ids`: A list of UUIDs representing the derived content IDs for which chunks and embeddings need to be copied.
- **Control Flow**:
    - Iterates over each derived content ID in the `derived_content_ids` list.
    - For each derived content ID, it prints a message indicating the start of the copying process.
    - Executes a SQL query on the `source_session` to select all `ChunkAndEmbedding` records associated with the current derived content ID.
    - Prints the number of chunks retrieved for the current derived content ID.
    - Creates a new list of `ChunkAndEmbedding` objects by copying the attributes of each chunk retrieved from the source.
    - Adds all new chunk objects to the `destination_session`.
    - Flushes the `destination_session` to persist the changes to the database.
- **Output**:
    - The function does not return any value; it performs database operations to copy data from the source to the destination session.


---
### copy_codebase 
The `copy_codebase` function duplicates a given codebase with updated attributes into a new session.
- **Inputs**:
    - `destination_session`: A `Session` object representing the database session where the new codebase will be added.
    - `codebase`: A `Codebase` object representing the codebase to be copied.
    - `new_workspace_id`: A `UUID` representing the new workspace ID to be assigned to the copied codebase.
    - `new_storage_url`: A `str` representing the new storage URL to be assigned to the copied codebase.
    - `new_creator_id`: A `str` representing the new creator ID to be assigned to the copied codebase.
- **Control Flow**:
    - The function updates the `workspace_id`, `storage_url`, and `creator_id` attributes of the `codebase` object with the new values provided as arguments.
    - A new `Codebase` object is created using the updated attributes of the original `codebase` object.
    - The new `Codebase` object is added to the `destination_session`.
    - The `flush` method is called on the `destination_session` to persist the changes to the database.
- **Output**:
    - The function does not return any value; it modifies the database session by adding a new codebase.


---
### copy_derived_content 
The `copy_derived_content` function copies derived content records to a new workspace in a destination session, handling records with and without source content dependencies separately.
- **Inputs**:
    - `destination_session`: A SQLAlchemy Session object representing the destination database session where the derived content will be copied to.
    - `derived_contents`: A list of DerivedContent objects that need to be copied to the new workspace.
    - `new_workspace_id`: A UUID representing the ID of the new workspace to which the derived content will be associated.
- **Control Flow**:
    - The function first separates the derived contents into two groups: those without a source_content_id (no dependency) and those with a source_content_id (dependent on earlier insertions).
    - For each content in the no_source_content group, it updates the workspace_id to the new_workspace_id, creates a new DerivedContent object with the updated data, and adds it to the destination session.
    - The destination session is flushed to ensure that the no_source_content records are inserted into the database before processing the dependent records.
    - For each content in the has_source_content group, it similarly updates the workspace_id, creates a new DerivedContent object, and adds it to the destination session.
    - The destination session is flushed again to insert the has_source_content records into the database.
- **Output**:
    - The function does not return any value; it performs operations directly on the destination session to copy the derived content records.


---
### generate_content_type_mapping 
The function generates a mapping of content type IDs from a source database session to a destination database session based on type names.
- **Inputs**:
    - `source_session`: A SQLAlchemy Session object connected to the source database, used to query content types.
    - `destination_session`: A SQLAlchemy Session object connected to the destination database, used to query content types.
- **Control Flow**:
    - Retrieve all content types from the source database using the source_session and store them in source_content_types.
    - Retrieve all content types from the destination database using the destination_session and store them in destination_content_types.
    - Create a dictionary, destination_mapping, mapping type names to their IDs from the destination content types.
    - Iterate over each content type in source_content_types.
    - For each source content type, check if its type name exists in destination_mapping.
    - If the type name exists, map the source content type ID to the corresponding destination content type ID in source_to_destination_mapping.
    - If the type name does not exist in destination_mapping, raise a ValueError indicating the missing content type.
    - Return the source_to_destination_mapping dictionary.
- **Output**:
    - A dictionary mapping content type IDs from the source to the destination based on matching type names.


---
### main 
The `main` function orchestrates the migration of codebase data and associated files from a source to a target environment, with options to skip database or S3 operations.
- **Inputs**:
    - `org_id`: A string representing the organization ID for which the data migration is to be performed.
    - `codebase_id`: A UUID representing the codebase ID to be migrated.
    - `skip_db`: A boolean flag indicating whether to skip the database migration process.
    - `skip_s3`: A boolean flag indicating whether to skip the S3 file synchronization process.
- **Control Flow**:
    - Retrieve source and target database URLs from environment variables.
    - Print a message indicating the start of migration for the given organization and codebase IDs.
    - Generate a bucket name using a SHA-256 hash of the organization ID and construct a new storage URL.
    - If `skip_db` is False, create database engine connections for both source and target databases.
    - Open sessions for both source and destination databases, and begin a transaction in the destination session.
    - Check if a default workspace exists in the destination database for the given organization ID; if not, create and commit a new default workspace.
    - Call `migrate_codebase_data` to handle the migration of codebase data from source to destination databases.
    - If `skip_s3` is False, call `sync_s3_to_minio` to synchronize S3 files from the source to the target environment.
- **Output**:
    - The function does not return any value; it performs side effects such as database migrations and S3 file synchronization.


---
### migrate_codebase_data 
The `migrate_codebase_data` function migrates a codebase and its related content from a source database to a destination database, updating necessary fields and copying associated data.
- **Inputs**:
    - `source_session`: A SQLAlchemy Session object connected to the source database.
    - `destination_session`: A SQLAlchemy Session object connected to the destination database.
    - `codebase_id`: A UUID representing the ID of the codebase to be migrated.
    - `new_workspace_id`: A UUID representing the new workspace ID for the migrated codebase.
    - `new_storage_url`: A string representing the new storage URL for the migrated codebase.
    - `new_creator_id`: A string representing the new creator ID for the migrated codebase.
- **Control Flow**:
    - Generate a mapping of content type IDs from the source to the destination using `generate_content_type_mapping` function.
    - Fetch the codebase and its associated derived content from the source database using the provided `codebase_id`.
    - Filter derived content to identify those that need embedding based on specific content type names.
    - Update the content type IDs in the derived content using the generated mapping.
    - Copy the codebase to the destination database with updated fields using `copy_codebase` function.
    - Copy the derived content to the destination database, ensuring proper order, using `copy_derived_content` function.
    - Copy the chunks and embeddings for each derived content that requires embedding using `copy_chunks_and_embeddings` function.
    - Commit the transaction to the destination database unless an exception occurs, in which case rollback the transaction.
- **Output**:
    - The function does not return any value; it performs database operations to migrate data and commits the transaction to the destination database.


---
### sync_s3_to_minio 
The function sync_s3_to_minio synchronizes files from an S3 bucket to a MinIO storage by downloading them locally and then uploading them to the target storage.
- **Inputs**:
    - `bucket_name`: The name of the S3 bucket from which files are to be synchronized.
    - `codebase_id`: A UUID representing the prefix used to filter objects in the S3 bucket for synchronization.
- **Control Flow**:
    - Initialize a boto3 session for the source S3 bucket using environment variables for AWS credentials.
    - Initialize a boto3 session for the target MinIO storage using environment variables for AWS credentials and endpoint URL.
    - Access the source S3 bucket and filter objects using the provided codebase_id as a prefix.
    - For each object, check if the local directory exists, create it if not, and download the file to the local system.
    - Store the downloaded file paths in a list.
    - Check if the target bucket exists in MinIO; if not, create it.
    - Upload each downloaded file from the local system to the target MinIO bucket.
    - Remove the local directory used for temporary storage of downloaded files.
- **Output**:
    - The function does not return any value; it performs file synchronization as a side effect.


---
### update_content_types 
The `update_content_types` function updates the content type IDs of derived content objects based on a provided mapping.
- **Inputs**:
    - `derived_contents`: A list of `DerivedContent` objects whose content type IDs need to be updated.
    - `content_type_mapping`: A dictionary mapping old content type IDs to new content type IDs.
- **Control Flow**:
    - Iterate over each `DerivedContent` object in the `derived_contents` list.
    - Check if the `content_type_id` of the current `DerivedContent` object exists in the `content_type_mapping` dictionary.
    - If it exists, update the `content_type_id` of the `DerivedContent` object to the corresponding value from the `content_type_mapping`.
    - If it does not exist, raise a `ValueError` indicating that the content type ID was not found in the mapping.
- **Output**:
    - The function does not return any value; it modifies the `content_type_id` of the `DerivedContent` objects in place or raises an exception if a mapping is not found.


