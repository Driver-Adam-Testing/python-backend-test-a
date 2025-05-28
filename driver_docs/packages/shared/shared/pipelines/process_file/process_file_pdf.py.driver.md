# Purpose
This Python script is designed to process PDF files by extracting and summarizing their content, including text, images, and tables. It leverages various libraries such as `fitz` for PDF manipulation, `PIL` for image processing, and `openai` for utilizing OpenAI's language models to generate summaries. The script defines a series of functions that handle different aspects of PDF processing: splitting PDFs into individual pages, converting pages to images, extracting text and images, and summarizing content using OpenAI's models. It also includes functionality to validate the generated summaries to ensure they accurately reflect the content of the PDF.

The script is structured to handle both text and visual content within PDFs, providing detailed descriptions and summaries of each component. It uses concurrent processing to efficiently handle multiple pages and images, making it suitable for large documents. The script is intended to be part of a larger system, as indicated by its use of shared modules and external services like OpenAI and Modal. It does not define a public API but rather serves as a backend utility for processing and summarizing PDF content, likely to be integrated into a larger application or service.
# Imports and Dependencies

---
- `base64`
- `concurrent.futures`
- `io`
- `os`
- `time`
- `fitz`
- `modal`
- `openai`
- `PIL`
- `pydantic`
- `shared.agent.agent_openai_strict`
- `shared.agent.models.openai.file_search`
- `shared.interfaces.agents.data_scope`
- `shared.interfaces.file_content.pdf_file_content`
- `shared.utils.openai_file`
- `tabula`


# Global Variables

---
### DESCRIBE_IMAGE_PROMPT 
- **Type**: `str`
- **Description**: `DESCRIBE_IMAGE_PROMPT` is a string variable that contains a detailed prompt for describing images. It provides guidelines for describing various types of images, including photographs, artwork, diagrams, charts, and technical illustrations, by specifying the type, layout, components, and any notable visual elements.
- **Use**: This variable is used as a prompt to guide the description of images in the `summarize_images` function, ensuring comprehensive and detailed image descriptions.


---
### SUMMARIZE_PDF_PROMPT 
- **Type**: `str`
- **Description**: `SUMMARIZE_PDF_PROMPT` is a string variable that contains a detailed prompt for analyzing and summarizing the contents of a PDF file. The prompt guides the analysis to cover various aspects of the document, such as its main focus, key themes, sections, and visual content.
- **Use**: This variable is used as a prompt for functions that perform PDF summarization, providing a structured guideline for extracting and summarizing information from PDF documents.


---
### assistant 
- **Type**: `OpenAI Assistant`
- **Description**: The `assistant` variable is an instance of an OpenAI Assistant created using the OpenAI client. It is configured with a specific name, instructions, model, and tools to perform tasks related to summarizing PDF documents.
- **Use**: This variable is used to create and manage an OpenAI Assistant that can process and summarize PDF files by interacting with the OpenAI API.


---
### client 
- **Type**: `OpenAI`
- **Description**: The `client` variable is an instance of the OpenAI class, which is likely used to interact with OpenAI's API services. This instance is created at the global scope, making it accessible throughout the module for various operations related to OpenAI's functionalities.
- **Use**: This variable is used to create and manage interactions with OpenAI's API, such as creating assistants and generating chat completions.


# Classes

---
### SummaryValidation 
- **Type**: `class`
- **Members**:
    - `is_valid_summary_of_a_file`: A boolean indicating if the text is a valid summary of a file.
- **Description**: The `SummaryValidation` class is a simple data model that inherits from `BaseModel` and is used to validate whether a given text is a valid summary of a file. It contains a single boolean attribute, `is_valid_summary_of_a_file`, which is set to `True` if the text is a valid summary and `False` if the text indicates missing or inaccessible information.
- **Inherits From**:
    - BaseModel


# Functions

---
### extract_images_from_pdf 
The `extract_images_from_pdf` function extracts all images from a PDF file and returns them as a list of `BytesIO` objects.
- **Inputs**:
    - `file_content`: A `BytesIO` object representing the content of the PDF file from which images are to be extracted.
- **Control Flow**:
    - Open the PDF document using the `fitz` library with the provided `file_content`.
    - Initialize an empty list `images` to store the extracted images.
    - Iterate over each page in the PDF document.
    - For each page, retrieve the list of images using `page.get_images(full=True)`.
    - For each image in the list, extract the image data using `pdf_document.extract_image(xref)`.
    - Create a `BytesIO` object for each extracted image, set its name, and append it to the `images` list.
    - Return the list of `BytesIO` objects containing the extracted images.
- **Output**:
    - A list of `BytesIO` objects, each containing the binary data of an extracted image from the PDF, with the `name` attribute set to a filename based on the original PDF file name and image index.


---
### extract_tables_from_pdf 
The `extract_tables_from_pdf` function extracts tables from a PDF file using the Tabula library.
- **Inputs**:
    - `file_content`: A `io.BytesIO` object representing the content of the PDF file from which tables are to be extracted.
- **Control Flow**:
    - The function imports the Tabula library, which is required for reading tables from PDFs.
    - It attempts to read all tables from the PDF file using `tabula.read_pdf` with the `pages="all"` and `multiple_tables=True` options.
    - If an exception occurs during table extraction, the function returns an empty list.
    - If tables are successfully extracted, it returns the list of tables; otherwise, it returns an empty list.
- **Output**:
    - A list of tables extracted from the PDF, or an empty list if no tables are found or an error occurs.


---
### extract_text_from_pdf 
The function `extract_text_from_pdf` extracts and returns all text from a PDF file provided as a byte stream.
- **Inputs**:
    - `file_content`: A `io.BytesIO` object representing the PDF file content to be processed.
- **Control Flow**:
    - Open the PDF document using the `fitz` library with the provided byte stream.
    - Initialize an empty string `all_text` to accumulate text from the PDF.
    - Iterate over each page in the PDF document using a loop.
    - For each page, load the page and extract its text using `get_text()`, appending it to `all_text`.
    - After processing all pages, return the accumulated text in `all_text`.
- **Output**:
    - A string containing all the text extracted from the PDF file.


---
### pdf_page_to_image 
The `pdf_page_to_image` function converts each page of a PDF file into a JPEG image and returns a list of these images as `BytesIO` objects.
- **Inputs**:
    - `file_content`: A `BytesIO` object containing the binary content of a PDF file.
- **Control Flow**:
    - Open the PDF document from the `BytesIO` stream using the `fitz` library.
    - Initialize an empty list `images` to store the converted images.
    - Iterate over each page in the PDF document.
    - For each page, load the page and create a pixmap representation of it.
    - Convert the pixmap to an RGB image using the `PIL` library.
    - Check if the image size exceeds 2048 pixels in any dimension, and if so, resize it to fit within 2048 pixels while maintaining aspect ratio.
    - Save the image as a JPEG into a new `BytesIO` object, set its name to indicate the page number, and append it to the `images` list.
    - Return the list of `BytesIO` objects containing the JPEG images.
- **Output**:
    - A list of `BytesIO` objects, each containing a JPEG image of a PDF page.


---
### process_extracted_tables 
The function `process_extracted_tables` extracts tables from a PDF page and returns them as a list of `ProcessedPdfFileContent` objects.
- **Inputs**:
    - `page_content`: A `BytesIO` object representing the content of a PDF page from which tables are to be extracted.
    - `index`: An integer representing the page number index, used to label the page in the output.
- **Control Flow**:
    - Initialize an empty list `table_contents` to store processed table data.
    - Iterate over each table extracted from the PDF page using `extract_tables_from_pdf(page_content)`.
    - For each table, create a `ProcessedPdfFileContent` object with the table content converted to a string, the page number incremented by one, and the content type set to `ProcessedPdfFileContentType.EXTRACTED_TABLE`.
    - Append each `ProcessedPdfFileContent` object to the `table_contents` list.
    - Return the `table_contents` list containing all processed tables.
- **Output**:
    - A list of `ProcessedPdfFileContent` objects, each representing a table extracted from the PDF page.


---
### process_extracted_text 
The function `process_extracted_text` extracts text from a PDF page and returns it as a `ProcessedPdfFileContent` object with metadata.
- **Inputs**:
    - `page_content`: A `BytesIO` object representing the content of a single page of a PDF file.
    - `index`: An integer representing the zero-based index of the page within the PDF document.
- **Control Flow**:
    - The function calls `extract_text_from_pdf` with `page_content` to extract text from the PDF page.
    - It creates a `ProcessedPdfFileContent` object with the extracted text, the page number (index + 1), and the content type set to `EXTRACTED_TEXT`.
    - The function returns the `ProcessedPdfFileContent` object.
- **Output**:
    - A `ProcessedPdfFileContent` object containing the extracted text, the page number, and the content type as `EXTRACTED_TEXT`.


---
### process_image 
The `process_image` function processes an image from a PDF page, generates a summary of the image, and returns it as a `ProcessedPdfFileContent` object.
- **Inputs**:
    - `image`: An `io.BytesIO` object representing the image data of a PDF page.
    - `index`: An integer representing the page number of the PDF from which the image was extracted, zero-based.
- **Control Flow**:
    - The function begins by printing a message indicating the processing of the current page (index + 1).
    - It calls the `summarize_images` function with the image and a prompt to generate a summary of the image.
    - If the image summary is successfully generated, it returns a `ProcessedPdfFileContent` object containing the summary, the page number (index + 1), and the content type as `EXTRACTED_IMAGE_SUMMARY`.
    - If an exception occurs during processing, it prints an error message and returns `None`.
- **Output**:
    - The function returns a `ProcessedPdfFileContent` object containing the image summary, page number, and content type, or `None` if an error occurs.


---
### process_visual_summary 
The `process_visual_summary` function processes a PDF page to generate a visual summary using a summarization query and an assistant ID.
- **Inputs**:
    - `page_content`: An `io.BytesIO` object representing the content of a single page of a PDF file.
    - `index`: An integer representing the page number index, used to identify the page in the PDF.
    - `summarization_query`: A string containing the query or prompt used to guide the summarization process.
    - `assistant_id`: An optional string representing the ID of the assistant used for summarization, or `None` if not applicable.
- **Control Flow**:
    - The function attempts to create a `ProcessedPdfFileContent` object by calling `summarize_pdf_with_retry` with the provided `page_content`, `summarization_query`, and `assistant_id`.
    - If `summarize_pdf_with_retry` successfully returns a summary, it is used to create a `ProcessedPdfFileContent` object with the page number incremented by one and the content type set to `VISUAL_SUMMARY`.
    - If an exception occurs during the summarization process, the function catches it and returns `None`.
- **Output**:
    - The function returns a `ProcessedPdfFileContent` object containing the visual summary of the PDF page, or `None` if an error occurs during processing.


---
### run_process_pdf 
The `run_process_pdf` function processes a PDF file to generate summaries and extract content such as text, images, and tables, handling exceptions and using concurrent processing for efficiency.
- **Inputs**:
    - `file_content`: A `io.BytesIO` object representing the PDF file content to be processed.
- **Control Flow**:
    - Initialize an empty list `processed_contents` to store processed content.
    - Attempt to summarize the entire PDF using `summarize_pdf_with_retry`; if an exception occurs, log the exception details and send an email notification.
    - If the whole file summary is not available, split the PDF into pages, extract images, summarize the images, and append the image summary to `processed_contents`.
    - If the whole file summary is available, append it to `processed_contents` as a visual summary.
    - Split the PDF into individual pages and use a `ThreadPoolExecutor` to concurrently process each page for images, text, and tables.
    - For each page, convert it to an image and submit tasks to process the image, extract text, and extract tables.
    - Collect results from the concurrent tasks and append them to `processed_contents`.
    - Print the processed contents and return them.
- **Output**:
    - A list of `ProcessedPdfFileContent` objects, each containing processed content from the PDF, such as summaries, extracted text, images, and tables.


---
### split_pdf_into_pages 
The function `split_pdf_into_pages` splits a PDF file into individual pages, each saved as a separate PDF file in memory.
- **Inputs**:
    - `file_content`: A `io.BytesIO` object containing the binary content of the PDF file to be split.
- **Control Flow**:
    - Open the PDF document from the provided `file_content` using the `fitz` library.
    - Initialize an empty list `created_pages` to store the individual page files.
    - Iterate over each page in the PDF document using a loop.
    - For each page, create a new PDF document and insert the current page into it.
    - Save the single-page PDF into a `BytesIO` object and reset its position to the start.
    - Name the `BytesIO` object using the original file name with a suffix indicating the page number.
    - Append the `BytesIO` object to the `created_pages` list.
    - Return the list `created_pages` containing all the individual page files.
- **Output**:
    - A list of `io.BytesIO` objects, each representing a single page of the original PDF file, saved as a separate PDF.


---
### summarize_images 
The `summarize_images` function encodes a list of images and a prompt into a format suitable for an OpenAI model to generate a summary of the images.
- **Inputs**:
    - `images`: A list of `io.BytesIO` objects representing the images to be summarized.
    - `prompt`: An optional string that provides a prompt for the image summarization; if not provided, a default prompt is used.
- **Control Flow**:
    - Initialize an empty list `encoded_images` to store encoded image data.
    - Iterate over each image in the `images` list.
    - For each image, read and encode the image data to a base64 string.
    - Determine the image's file extension to set the appropriate media type (e.g., 'image/jpeg', 'image/png').
    - If the image type is unsupported, print a message and skip to the next image.
    - Append a dictionary with the encoded image data and media type to `encoded_images`.
    - Append a dictionary with the prompt text to `encoded_images`, using the provided prompt or a default prompt if none is provided.
    - Send the `encoded_images` list to the OpenAI model to generate a summary, specifying the model and message format.
    - Return the content of the first choice from the model's response.
- **Output**:
    - A string containing the summary of the images generated by the OpenAI model.


---
### summarize_pdf_with_retry 
The function `summarize_pdf_with_retry` attempts to summarize a PDF file by querying an external service, retrying up to three times if necessary, and returns the summary if successful.
- **Inputs**:
    - `file_content`: A `io.BytesIO` object representing the content of the PDF file to be summarized.
    - `summarization_query`: A string containing the query or prompt to be used for summarizing the PDF file.
    - `assistant_id`: A string representing the identifier of the assistant to be used for querying the file.
- **Control Flow**:
    - Initialize the number of attempts to 3.
    - Upload the PDF file content to an external service to obtain a file ID.
    - Iterate up to 3 times to attempt summarizing the PDF file.
    - In each attempt, try to query the file using the file ID, summarization query, and assistant ID to get a summary.
    - Validate the obtained summary using the `validate_summary` function.
    - If the summary is valid, return it immediately.
    - If the summary is not valid, raise an exception to trigger a retry.
    - If an exception occurs and the maximum number of attempts is not reached, print an error message and wait for 30 seconds before retrying.
    - If all attempts fail, print a final error message.
- **Output**:
    - Returns a string containing the summary of the PDF file if successful, or `None` if all attempts fail.


---
### validate_summary 
The `validate_summary` function checks if a given text is a valid summary of a file using an OpenAI agent.
- **Inputs**:
    - `summary`: A string representing the text to be validated as a summary of a file.
- **Control Flow**:
    - An `OpenAIStrictAgent` is instantiated with specific parameters including a model, response format, and data scope.
    - The agent is invoked with a command to return a `ValidateSummary` object based on the provided summary text.
    - The function returns the `is_valid_summary_of_a_file` attribute from the `ValidateSummary` object, indicating whether the summary is valid.
- **Output**:
    - A boolean value indicating whether the provided summary is a valid summary of a file.


