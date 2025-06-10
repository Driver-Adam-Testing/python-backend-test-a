# Purpose
This Python code file is designed to handle the processing and embedding of PDF summaries within a cloud-based application environment, specifically using the Modal framework. The file defines two main functions: `send_exception_email` and `create_and_embed_pdf_summaries`. The `send_exception_email` function is responsible for sending email notifications via SendGrid when exceptions occur, providing a mechanism for error reporting and alerting. The `create_and_embed_pdf_summaries` function is the core of the file, tasked with downloading a PDF from a presigned URL, sanitizing it using Ghostscript, and then processing the PDF to extract and embed its content. This involves splitting the text, embedding it using a text embedding service, and persisting the results to a database. The function also manages the status of the processing task, updating it in the database as it progresses.

The code leverages several external libraries and services, including AWS S3 for file storage, SQLAlchemy for database interactions, and concurrent futures for parallel processing. It is structured to be executed within a Modal application, utilizing Modal's capabilities for containerized execution and secret management. The file is not a standalone script but rather a component of a larger system, likely intended to be deployed in a cloud environment where it can be triggered to process PDF files as part of a data pipeline. The use of Modal's application and function decorators indicates that this code is designed to be part of a scalable, distributed system, with specific configurations for container images, secrets, and resource limits.
# Imports and Dependencies

---
- `concurrent.futures`
- `os`
- `pathlib.Path`
- `modal`
- `sendgrid`
- `sendgrid.helpers.mail.Content`
- `sendgrid.helpers.mail.Email`
- `sendgrid.helpers.mail.Mail`
- `sendgrid.helpers.mail.To`
- `io`
- `hashlib.sha256`
- `tempfile.NamedTemporaryFile`
- `database.db.engine`
- `database.models_v1.ChunkAndEmbedding`
- `database.models_v1.DerivedContent`
- `database.models_v2.Node`
- `database.models_v2.Version`
- `database.models_v2_enums.ContentKind`
- `database.models_v2_enums.NodeKind`
- `database.models_v2_enums.VersionStatus`
- `shared.chunking.text_splitter.split_text`
- `shared.embedding.text_embedder.batch_embed_text`
- `shared.file_storage.aws_s3_client.AWSS3Client`
- `shared.interfaces.aws_client_config.AWSClientConfig`
- `shared.interfaces.file_content.pdf_file_content.ProcessedPdfFileContent`
- `shared.pipelines.process_file.process_file_pdf.run_process_pdf`
- `sqlalchemy.orm.selectinload`
- `sqlmodel.Session`
- `sqlmodel.select`
- `subprocess`


# Global Variables

---
### app 
- **Type**: `modal.App`
- **Description**: The `app` variable is an instance of the `modal.App` class, initialized with the name 'pdf-summary-embedding'. This instance is used to define and manage functions that are executed within the Modal framework, which is a platform for running serverless applications.
- **Use**: This variable is used to register functions that can be executed as part of the serverless application, such as `send_exception_email` and `create_and_embed_pdf_summaries`.


---
### image_jve 
- **Type**: `modal.Image`
- **Description**: The `image_jve` variable is an instance of `modal.Image` configured with a Debian Slim base image and Python version 3.12. It includes additional local directories copied to specified remote paths and installs dependencies from a `pyproject.toml` file, as well as additional packages like the default Java Runtime Environment and Ghostscript.
- **Use**: This variable is used to define the environment configuration for running tasks in the Modal application, particularly for PDF processing and embedding.


---
### pdf_preprocessing_modal_config 
- **Type**: `dict`
- **Description**: The `pdf_preprocessing_modal_config` is a dictionary that holds configuration settings for a Modal function related to PDF preprocessing. It includes an image configuration, a list of secrets for secure access to various services, a proxy configuration based on the environment, and a limit on the maximum number of containers that can be used.
- **Use**: This variable is used to configure the `create_and_embed_pdf_summaries` function, providing necessary settings for image, secrets, proxy, and container limits.


# Functions

---
### create_and_embed_pdf_summaries 
The function `create_and_embed_pdf_summaries` processes a PDF file from a presigned URL, sanitizes it, embeds its content, and stores the results in a database while handling exceptions.
- **Inputs**:
    - `presigned_url`: A string representing the presigned URL to download the PDF file.
    - `version_id`: A string representing the version ID of the asset being processed.
    - `asset_name`: A string representing the name of the asset (PDF file) being processed.
    - `org_id`: A string representing the organization ID, used for hashing and bucket naming.
- **Control Flow**:
    - Hash the organization ID to create a unique bucket name.
    - Open a database session to retrieve the version and primary asset ID using the provided version ID.
    - Download the PDF file from the presigned URL to a temporary file.
    - Sanitize the PDF using Ghostscript and upload both sanitized and unsanitized versions to S3.
    - Update the version status to 'GENERATING' and create a new node in the database.
    - Read the PDF content and process it to extract and embed text using a thread pool executor.
    - Persist the processed content and embeddings to the database using another thread pool executor.
    - Update the version status to 'GENERATION_COMPLETE' after successful processing.
    - Handle exceptions by logging details, sending an email notification, and updating the version status to 'GENERATION_ERROR'.
- **Output**:
    - The function does not return any value; it performs operations and updates the database.


---
### persist_to_db 
The `persist_to_db` function saves processed PDF content and its associated text splits and embeddings into a database.
- **Inputs**:
    - `result`: An instance of `ProcessedPdfFileContent` containing the processed content of a PDF file.
    - `splits`: A list of text splits derived from the PDF content.
    - `embeds`: A list of embeddings corresponding to the text splits.
- **Control Flow**:
    - Open a database session using the `Session` context manager.
    - Retrieve the content type from the `result` and check if it exists in the `ContentKind` enum; raise an exception if not.
    - Clean the content by removing NUL characters.
    - Create a `DerivedContent` object with the cleaned content and metadata, then add it to the session.
    - Commit the session to save the `DerivedContent` to the database and refresh it to get the generated ID.
    - If embeddings are provided, iterate over the `splits` and `embeds`, creating `ChunkAndEmbedding` objects for each and adding them to the session.
    - Commit the session again to save the `ChunkAndEmbedding` objects to the database.
- **Output**:
    - The function does not return any value; it performs database operations to persist data.


---
### sanitize_pdf_with_ghostscript 
The function `sanitize_pdf_with_ghostscript` uses Ghostscript to sanitize a PDF file by processing it and saving the output to a specified destination path.
- **Inputs**:
    - `file_path`: A `Path` object representing the path to the input PDF file that needs to be sanitized.
    - `destination_path`: A `Path` object representing the path where the sanitized PDF file will be saved.
- **Control Flow**:
    - Import the `subprocess` module to execute system commands.
    - Define the Ghostscript command with options to process the PDF without pausing, in batch mode, and specifying the output device as `pdfwrite`.
    - Set the output file path using the `-sOUTPUTFILE` option and include the input file path in the command.
    - Execute the command using `subprocess.run` with `check=True` to raise an exception on failure, and capture the output and error messages.
    - If the command execution fails, catch the `subprocess.CalledProcessError` exception, print the error details including return code, stdout, and stderr, and re-raise the exception.
    - If the command executes successfully, print a success message.
- **Output**:
    - The function does not return any value; it performs its operation as a side effect by creating a sanitized PDF file at the specified destination path.


---
### send_exception_email 
The `send_exception_email` function sends an email notification about an exception using the SendGrid API.
- **Inputs**:
    - `exception_details`: A string containing details about the exception that occurred.
- **Control Flow**:
    - Import necessary modules from SendGrid for email handling.
    - Retrieve environment variables for environment name and SendGrid API key.
    - Initialize the SendGrid API client using the API key.
    - Set up the email details including sender, recipient, subject, and content using the provided exception details.
    - Attempt to send the email using the SendGrid client and print the response status code if successful.
    - Catch any exceptions during the email sending process and print an error message.
- **Output**:
    - The function does not return any value; it performs side effects by sending an email and printing status messages.


