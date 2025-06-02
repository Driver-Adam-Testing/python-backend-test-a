# Purpose
This Python script is a comprehensive tool designed for automated documentation generation, particularly for software projects. It leverages various libraries and APIs, including OpenAI, Google Gemini, and AWS S3, to analyze codebases and generate structured documentation. The script is organized into several classes and functions that handle different aspects of the documentation process, such as configuration management, section creation, and content aggregation.

The script's primary functionality is encapsulated in the `AutoDocInitState` class, which orchestrates the entire documentation generation process. It supports multiple modes of operation, including validating configuration files, executing documentation generation, and resuming previous sessions. The script uses asynchronous programming to efficiently handle tasks like annotating files for relevance, generating initial section drafts, and updating sections with detailed content. It also includes mechanisms for handling large codebases and PDFs, ensuring that the generated documentation is both comprehensive and well-structured. The script is intended to be run as a standalone tool, with command-line arguments specifying the desired operation mode.
# Imports and Dependencies

---
- `argparse`
- `asyncio`
- `copy`
- `hashlib`
- `json`
- `os`
- `tempfile`
- `tomllib`
- `collections.abc`
- `enum`
- `graphlib`
- `pathlib`
- `typing`
- `boto3`
- `openai`
- `pymupdf4llm`
- `aiolimiter`
- `database.models_v2_enums`
- `google`
- `pydantic`
- `rich.console`
- `rich.markdown`
- `shared.chunking.text_splitter`
- `tqdm.asyncio`
- `utils.models`
- `modal`
- `database.db`
- `database.models_v2`
- `sqlmodel.ext.asyncio.session`
- `sqlmodel`
- `database.models_v1`
- `database.models_v2`
- `sqlalchemy.orm`


# Global Variables

---
### ARCHITECTURE 
- **Type**: ``StrEnum``
- **Description**: `ARCHITECTURE` is a member of the `DocKind` enumeration class, which is a subclass of `StrEnum`. This enumeration is used to define different kinds of document formats or types that can be used in the software's documentation process.
- **Use**: `ARCHITECTURE` is used to specify a document type related to architecture within the `DocKind` enumeration.


---
### BLUE 
- **Type**: `str`
- **Description**: The variable `BLUE` is a string that contains the ANSI escape code for the color blue. It is defined as `"\033[94m"`, which is used to change the text color in terminal outputs to blue.
- **Use**: This variable is used to format text output in the terminal with a blue color.


---
### CODE_EXAMPLE 
- **Type**: ``SectionCreationMethod``
- **Description**: `SectionCreationMethod` is an enumeration class that defines different methods for creating sections in a document. It includes four possible values: `SEQUENTIAL_EDIT`, `SCATTER_GATHER`, `ONLY_PDFS`, and `CODE_EXAMPLE`. Each value represents a distinct approach to section creation, such as sequential editing, gathering content from multiple sources, using only PDFs, or focusing on code examples.
- **Use**: This variable is used to specify the method by which sections of a document are created, allowing for different strategies in content generation.


---
### CYAN 
- **Type**: `str`
- **Description**: The `CYAN` variable is a string that contains the ANSI escape code for the cyan color. This escape code is used to change the text color in terminal outputs to cyan, which is a shade of blue-green.
- **Use**: This variable is used to apply cyan color formatting to text output in the terminal.


---
### DEFINED_SECTIONS 
- **Type**: ``StrEnum``
- **Description**: `DEFINED_SECTIONS` is a member of the `DocKind` enumeration, which is a subclass of `StrEnum`. This enumeration is used to define different kinds of document formats or types that can be used in the application.
- **Use**: `DEFINED_SECTIONS` is used to specify a document type where sections are predefined, guiding how documents are structured and generated.


---
### FROM_EXAMPLE 
- **Type**: ``StrEnum``
- **Description**: `FROM_EXAMPLE` is a member of the `DocKind` enumeration, which is a subclass of `StrEnum`. This enumeration is used to define different kinds of document formats or types that the system can handle.
- **Use**: `FROM_EXAMPLE` is used to specify a document type that is derived from an example, likely indicating a specific format or structure for processing or generating documents.


---
### GREEN 
- **Type**: `str`
- **Description**: The variable `GREEN` is a string that represents the ANSI escape code for the color green. It is used to change the text color in terminal outputs to green.
- **Use**: This variable is used to format text output in the terminal with a green color.


---
### HighlyRelevant 
- **Type**: ``IntEnum``
- **Description**: `HighlyRelevant` is an enumeration member of the `Category` class, which is a subclass of `IntEnum`. It represents a category with a value of 0, indicating the highest level of relevance in the context of categorizing files or content for documentation purposes.
- **Use**: This variable is used to categorize files or content as highly relevant when assessing their importance for inclusion in a document section.


---
### Irrelevant 
- **Type**: ``IntEnum``
- **Description**: The `Irrelevant` variable is a member of the `Category` enumeration, which is a subclass of `IntEnum`. It represents a category with an integer value of 2, indicating that a file or content is not relevant for a specific purpose or context.
- **Use**: This variable is used to categorize files or content as irrelevant in the context of document generation or content evaluation.


---
### LOCAL 
- **Type**: ``ExecutionMode``
- **Description**: `ExecutionMode` is an enumeration class that defines two modes of execution: `LOCAL` and `MODAL`. These modes are used to specify the context in which certain operations or functions should be executed, such as determining file paths or handling execution logic.
- **Use**: This variable is used to determine the execution context for operations, affecting how file paths are resolved and how certain functions behave.


---
### LOCAL_FILES 
- **Type**: `dict[str, str]`
- **Description**: `LOCAL_FILES` is a global variable that is intended to store a dictionary mapping string keys to string values. It is initialized by attempting to load data from a JSON file named 'local_setup.json'. If the file is not found, `LOCAL_FILES` is set to `None`. This variable is used to store configuration or setup information that is expected to be available locally.
- **Use**: `LOCAL_FILES` is used to retrieve file paths or other configuration details from a local JSON file for use in various functions throughout the code.


---
### MODAL 
- **Type**: ``ExecutionMode``
- **Description**: `ExecutionMode` is an enumeration class that defines two possible modes of execution: `LOCAL` and `MODAL`. This class is used to specify the context or environment in which certain operations or functions should be executed.
- **Use**: This variable is used to determine the execution context for various functions, such as file path retrieval and document generation.


---
### ONLY_PDFS 
- **Type**: ``StrEnum``
- **Description**: `ONLY_PDFS` is a member of the `SectionCreationMethod` enumeration, which is a subclass of `StrEnum`. This enumeration is used to define different methods for creating sections in a document, with `ONLY_PDFS` indicating that the section should be created using only PDF content.
- **Use**: This variable is used to specify that a section should be created using only PDF content in the document generation process.


---
### OPENAI_LIMITER 
- **Type**: `AsyncLimiter`
- **Description**: `OPENAI_LIMITER` is an instance of the `AsyncLimiter` class, which is used to control the rate of requests to the OpenAI API. It is configured to allow up to 100 requests per second.
- **Use**: This variable is used to ensure that the application does not exceed the rate limit when making requests to the OpenAI API, by limiting the number of requests to 100 per second.


---
### OPENAI_SEM 
- **Type**: ``asyncio.Semaphore``
- **Description**: `OPENAI_SEM` is a global variable that is an instance of `asyncio.Semaphore` initialized with a value of 300. This semaphore is used to control access to a shared resource by limiting the number of concurrent tasks that can access it.
- **Use**: It is used to limit the number of concurrent asynchronous operations, specifically when generating responses with the `llm_generate` function.


---
### ORANGE 
- **Type**: `str`
- **Description**: The variable `ORANGE` is a string that represents an ANSI escape code for the color orange. Specifically, it uses the 256-color mode with the color code 214.
- **Use**: This variable is used to apply the orange color to text output in a terminal that supports ANSI escape codes.


---
### PDF_DOWNLOAD_DIR 
- **Type**: `str`
- **Description**: The `PDF_DOWNLOAD_DIR` variable is a string that specifies the directory path where PDF files are downloaded and stored. In this code, it is set to the relative path 'pdfs/'. This variable is used to define the location for storing PDF files that are downloaded from external sources, such as S3 buckets.
- **Use**: This variable is used to specify the directory path for storing downloaded PDF files.


---
### RED 
- **Type**: `str`
- **Description**: The variable `RED` is a string that represents the ANSI escape code for the color red. It is used to change the text color in terminal outputs to red.
- **Use**: This variable is used to format text output in the terminal with a red color.


---
### RESET 
- **Type**: `str`
- **Description**: The `RESET` variable is a string that contains the ANSI escape code `\033[0m`. This code is used to reset the terminal text color to its default setting after it has been changed by other ANSI color codes.
- **Use**: This variable is used to reset the terminal text color to default after using colored text.


---
### SCATTER_GATHER 
- **Type**: ``StrEnum``
- **Description**: `SCATTER_GATHER` is a member of the `SectionCreationMethod` enumeration, which is a subclass of `StrEnum`. This enumeration is used to define different methods for creating sections in a document.
- **Use**: `SCATTER_GATHER` is used to specify that a section should be created using the scatter-gather method, which involves writing sections based on individual files or pages and then aggregating them.


---
### SEQUENTIAL_EDIT 
- **Type**: ``StrEnum``
- **Description**: `SEQUENTIAL_EDIT` is a member of the `SectionCreationMethod` enumeration, which is a subclass of `StrEnum`. This enumeration is used to define different methods for creating sections in a document.
- **Use**: This variable is used to specify that a section should be created using a sequential editing method.


---
### SomewhatRelevant 
- **Type**: `IntEnum`
- **Description**: `SomewhatRelevant` is a member of the `Category` enumeration, which is an `IntEnum` class. It represents a category with a value of 1, indicating that a file or section is somewhat relevant to a specific context or task.
- **Use**: This variable is used to categorize files or sections as somewhat relevant in the context of document generation or content evaluation.


---
### UNDEFINED 
- **Type**: ``StrEnum``
- **Description**: `UNDEFINED` is a member of the `DocKind` enumeration class, which is a subclass of `StrEnum`. This enumeration is used to define different kinds of document formats or types that can be processed or generated by the system.
- **Use**: `UNDEFINED` is used to represent a document kind that does not fall into any of the predefined categories within the `DocKind` enumeration.


---
### args 
- **Type**: `argparse.Namespace`
- **Description**: The `args` variable is an instance of `argparse.Namespace` that holds the command-line arguments parsed by the `argparse` module. It is used to store the values of the command-line options and arguments provided by the user when running the script.
- **Use**: This variable is used to determine the execution path of the program based on the command-line arguments provided, such as validating a configuration file, executing content generation, or resuming execution.


---
### committed_with 
- **Type**: `str`
- **Description**: The `committed_with` variable is a string attribute of the `SectionCfg` class, which is a subclass of `BaseModel`. It is initialized to `None` by default.
- **Use**: This variable is used to determine if the `required` setting of a section should be ignored, based on whether `committed_with` is not `None`.


---
### mutex_group 
- **Type**: `argparse._MutuallyExclusiveGroup`
- **Description**: The `mutex_group` variable is an instance of `argparse._MutuallyExclusiveGroup`, which is used to create a group of arguments that are mutually exclusive, meaning only one of the arguments in the group can be specified at a time. This is part of the argument parsing setup in a command-line interface (CLI) application.
- **Use**: This variable is used to ensure that only one of the mutually exclusive command-line arguments (`--validate`, `--execute`, or `--resume`) is provided by the user when running the script.


---
### parser 
- **Type**: `argparse.ArgumentParser`
- **Description**: The `parser` variable is an instance of `argparse.ArgumentParser`, which is used to create a command-line interface for the script. It defines the arguments that the script can accept, including mutually exclusive options for validation, execution, and resumption of tasks, as well as a quiet mode option.
- **Use**: This variable is used to parse command-line arguments and determine the mode of operation for the script.


---
### required 
- **Type**: `bool`
- **Description**: The `required` variable is a boolean attribute within the `SectionCfg` class, which is a subclass of `BaseModel`. It is used to indicate whether a section is mandatory or not in the context of document generation.
- **Use**: This variable is used to determine if a section should be included by default when generating a document, unless overridden by the `committed_with` attribute.


# Classes

---
### AutoDocCfg 
- **Type**: `class`
- **Members**:
    - `llm`: An instance of LlmCfg representing the language model configuration.
    - `document`: An instance of DocumentCfg representing the document configuration.
    - `scope`: An instance of Scope representing the scope of the document.
    - `sections`: A list of SectionCfg instances representing the sections of the document.
- **Description**: The `AutoDocCfg` class is a configuration model for automated document generation, inheriting from `BaseModel`. It encapsulates configurations for language models, document structure, scope, and sections. The class provides methods to load configurations from a file, evaluate optional sections, and generate document sections asynchronously. It supports reading configurations from a TOML file, applying default settings, and formatting sections based on substitutions. The class is designed to facilitate the creation of structured documents by evaluating and including relevant sections based on the provided configurations.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### AutoDocCfg.eval_optional_sections
The `eval_optional_sections` function evaluates optional sections of a document configuration to determine which should be included based on relevance, using a language model.
- **Inputs**:
    - `self`: An instance of the `AutoDocCfg` class, which contains document configuration details.
    - `llm`: An instance of `ChatOpenAI`, representing the language model used for evaluation.
    - `long_descriptions`: A string containing long descriptions of the source code, used as context for evaluating the relevance of optional sections.
- **Control Flow**:
    - Extracts optional sections from the document configuration that are not required and not committed with any other section.
    - If there are optional sections, it prints their titles and evaluates them using the `SectionFlags.from_llm` method, which uses the language model to determine their relevance.
    - Iterates over the optional sections and their corresponding flags to check for any discrepancies in the evaluation results, raising a `ValueError` if any are found.
    - Adds the index of sections flagged as relevant to a set of included indices, printing a message for each section indicating whether it is included or not.
    - Checks for sections that are committed with other sections and adds them to the included indices if their parent sections are required or included.
    - Returns a list of `SectionCommitted` objects for sections that are required or included based on the evaluation.
- **Output**:
    - A list of `SectionCommitted` objects representing the sections that are determined to be included in the document.


---
#### AutoDocCfg.from_file
The `from_file` function reads a TOML configuration file, merges it with default settings, and returns an instance of the class with the combined configuration data.
- **Inputs**:
    - `cls`: The class to which this method belongs, used to create an instance of the class.
    - `toml_file`: A string representing the path to the TOML file to be read and processed.
- **Control Flow**:
    - Open the specified TOML file in binary read mode.
    - Load the contents of the file using the `tomllib.load` function into `raw_data`.
    - Retrieve the default configuration for `LlmCfg` and merge it with any existing 'llm' configuration in `raw_data`.
    - Retrieve the default configuration for `Scope` and merge it with any existing 'scope' configuration in `raw_data`.
    - Ensure that the 'sections' key exists in `raw_data`, defaulting to an empty list if not present.
    - Create an instance of the class (`cfg`) using the merged `raw_data`.
    - If 'substitutions' exist in `raw_data`, apply them to format the `instruction` and `content_structure` of each section in `cfg.sections`.
    - Return the configured instance `cfg`.
- **Output**:
    - An instance of the class (`cls`) initialized with the configuration data from the TOML file and default settings.



---
### AutoDocInitState 
- **Type**: `class`
- **Members**:
    - `llm`: Configuration for language models used in document generation.
    - `document`: Configuration for the document being generated, including goal and format.
    - `scope`: Defines the scope of the document, including preamble and code or PDF sources.
    - `sections`: List of committed sections to be included in the document.
- **Description**: The `AutoDocInitState` class is responsible for managing the initialization and state of an automated document generation process. It uses configurations for language models, document goals, and scope to generate a structured document from various sources, such as codebases and PDFs. The class provides methods to assemble system prompts, save and load state, and generate the final document by iteratively refining section drafts and performing copy editing.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### AutoDocInitState._annotate_file
The `_annotate_file` function asynchronously annotates a file by categorizing its relevance to different document sections using a language model.
- **Inputs**:
    - `llm`: An instance of `ChatOpenAI`, representing the language model used for generating annotations.
    - `node`: A tuple containing a string (node identifier) and a `TechDocsContent` object, which includes the source code and descriptions of the file to be annotated.
- **Control Flow**:
    - The function begins by extracting the `TechDocsContent` from the `node` tuple and asserts that the `source` attribute is not `None`.
    - It initializes an empty list `node_list` to store the annotations.
    - The source code of the file is split into chunks using the `split_text` function, with a specified chunk size and no overlap.
    - A user prompt is constructed using the short paragraph description and the first chunk of the source code.
    - An asynchronous task group is created to handle multiple annotation tasks concurrently.
    - For each section in `self.sections`, a task is created to generate an annotation using the `llm_generate` function, which takes the language model, a system prompt, and the user prompt as inputs.
    - The results of the annotation tasks are collected and converted into `Category` objects, which are then added to `node_list`.
    - If an exception occurs during the process, an error message is printed, and the function returns the node identifier with a list of `Category.Irrelevant` for each section.
    - Finally, the function returns a tuple containing the node identifier and the list of annotations.
- **Output**:
    - A tuple containing the node identifier (string) and a list of `Category` objects representing the relevance of the file to each document section.


---
#### AutoDocInitState._annotate_nodes
The `_annotate_nodes` function asynchronously annotates nodes and PDFs for relevance to document sections using a language model.
- **Inputs**:
    - `llm`: An instance of `ChatOpenAI` used for generating annotations.
    - `topo`: A list of tuples, each containing a node identifier and its associated `TechDocsContent`.
    - `graph`: A dictionary representing the graph structure, mapping node identifiers to sets of child node identifiers.
    - `execution_mode`: An `ExecutionMode` enum indicating the mode of execution, either LOCAL or MODAL.
    - `pdf_pages_dict`: A dictionary mapping PDF file paths to lists of their page contents as strings.
- **Control Flow**:
    - Prints a message indicating the start of file annotation.
    - Initializes dictionaries for storing tagged nodes and PDFs.
    - Creates coroutines for annotating files with non-null sources using `_annotate_file`.
    - Gathers results from file annotation coroutines and updates `tagged_nodes`.
    - Iterates over nodes to annotate folders based on their child nodes' relevance.
    - Checks if there are PDFs to annotate and prints a message if so.
    - Iterates over PDF paths, creating coroutines for annotating each page using `_annotate_pdf_page`.
    - Gathers results from PDF annotation coroutines and updates `tagged_pdfs`.
    - Returns the dictionaries `tagged_nodes` and `tagged_pdfs`.
- **Output**:
    - A tuple containing two dictionaries: `tagged_nodes` mapping node identifiers to lists of `Category` annotations, and `tagged_pdfs` mapping PDF paths to dictionaries of page indices and their `Category` annotations.


---
#### AutoDocInitState._annotate_pdf_page
The `_annotate_pdf_page` function asynchronously annotates a PDF page by categorizing its content into predefined categories using a language model.
- **Inputs**:
    - `llm`: An instance of `ChatOpenAI`, which is a language model used to generate responses for categorizing the PDF page content.
    - `pdf_text`: A string representing the text content of a single page from a PDF document that needs to be categorized.
    - `page_idx`: An integer representing the index of the page within the PDF document, used to identify the page in the output.
- **Control Flow**:
    - A user prompt is created by embedding the PDF page content into a predefined string format.
    - An empty list `annotation_task_list` is initialized to store tasks for each section's annotation.
    - An asynchronous task group is created to manage concurrent execution of tasks.
    - For each section in `self.sections`, a task is created to generate a response using the `llm_generate` function with the section's system prompt and the user prompt.
    - Each task is added to the `annotation_task_list`.
    - The tasks are awaited, and their results are collected into `annotations_list` by converting each result into a `Category` object.
    - The function returns a tuple containing the `page_idx` and the `annotations_list`.
- **Output**:
    - A tuple containing the page index and a list of `Category` objects representing the annotations for the PDF page.


---
#### AutoDocInitState._final_section_format
The `_final_section_format` function refines and formats the content of document sections using a language model to ensure they adhere to a specified structure.
- **Inputs**:
    - `self`: The instance of the class to which this method belongs, containing attributes like `sections`, `document`, and `scope`.
    - `llm`: An instance of `ChatOpenAI`, representing the language model used to generate responses.
    - `previous_state`: A list of dictionaries, each containing the 'order_idx', 'title', and 'content' of a document section, representing the current state of the sections before final formatting.
- **Control Flow**:
    - Assert that the length of `previous_state` matches the number of sections in `self.sections` to ensure consistency.
    - Initialize an empty list `prompt_pairs` to store tuples of system and user prompts for each section.
    - Iterate over each section in `previous_state`, asserting that the section titles match those in `self.sections`.
    - For each section, construct a `user_prompt` with the detailed content of the section and a `system_prompt` using the `final_output_format` method of the corresponding section in `self.sections`.
    - Append the tuple of `system_prompt` and `user_prompt` to `prompt_pairs`.
    - Create an asynchronous task group to handle the generation of formatted section content using the language model.
    - For each pair of prompts in `prompt_pairs`, create a task to generate the formatted content using `llm_generate` and add it to the task group.
    - Initialize an empty list `new_state` to store the results of the formatted sections.
    - Iterate over the completed tasks, appending a dictionary with the 'order_idx', 'title', and newly formatted 'content' to `new_state`.
    - Return `new_state`, which contains the formatted content for each section.
- **Output**:
    - A list of dictionaries, each containing the 'order_idx', 'title', and newly formatted 'content' of a document section.


---
#### AutoDocInitState._initialize_sections
The `_initialize_sections` function initializes document sections based on various section creation methods using provided data and configurations.
- **Inputs**:
    - `llm`: An instance of `ChatOpenAI` used for generating content for sections.
    - `reverse_topos_from_start`: A list of lists containing topologically sorted nodes in reverse order, representing the structure of the document sections.
    - `driver_docs`: A list of `DriverDocsContent` objects containing the content and structure of the codebase to be documented.
    - `annotations`: A dictionary mapping node names to lists of `Category` objects, indicating the relevance of each node to the document sections.
    - `pdf_annotations`: A dictionary containing annotations for PDF pages, indicating their relevance to the document sections.
    - `execution_mode`: An `ExecutionMode` enum indicating whether the execution is local or modal.
    - `pdf_pages_dict`: A dictionary mapping PDF file paths to lists of strings, where each string represents the content of a PDF page.
- **Control Flow**:
    - Check if PDFs are included in the scope and if any section uses the `ONLY_PDFS` method, then upload PDFs to a client if necessary.
    - Initialize empty dictionaries and sets for sections and nodes.
    - If any section uses the `SEQUENTIAL_EDIT` method, generate initial drafts for these sections using the LLM and add relevant nodes to the set.
    - If any section uses the `SCATTER_GATHER` method, create sections using scatter-gather approach and update the sections dictionary with results.
    - If any section uses the `CODE_EXAMPLE` method, generate code examples using a few-shot generator and update the sections dictionary with results.
    - For sections using the `ONLY_PDFS` method, generate content using a client model and update the sections dictionary with results.
    - Compile the initialized sections into a list, ensuring the order matches the section configuration.
    - Return the set of initialized nodes and the list of initialized sections.
- **Output**:
    - A tuple containing a set of initialized node names and a list of dictionaries, each representing an initialized section with its order index, title, and content.


---
#### AutoDocInitState._update_sections
The `_update_sections` function updates document sections based on new content from a specified node, using a language model to generate updated content for each section.
- **Inputs**:
    - `llm`: An instance of `ChatOpenAI`, representing the language model used to generate responses.
    - `node_name`: A string representing the name of the node whose content is used to update the sections.
    - `previous_state`: A list of dictionaries, each containing the current state of a document section with keys 'order_idx', 'title', and 'content'.
    - `tech_docs`: An instance of `TechDocsContent`, containing detailed content and source code for the node.
    - `annotations`: An optional list of `Category` enums indicating the relevance of each section to the node content, or None if not provided.
- **Control Flow**:
    - Assert that the length of `previous_state` matches the number of sections.
    - Initialize common prompts for updating and describing the node content.
    - Return `previous_state` if the node's source is empty or None.
    - Iterate over each section in `previous_state` to create prompts for updating the section content.
    - For each section, determine the system and user prompts based on whether the node has source content or not.
    - Create tasks to generate updated content for each section using the language model, skipping sections marked as irrelevant or not using SEQUENTIAL_EDIT method.
    - Collect results from the tasks and update the section content accordingly.
    - Return the updated state of the sections.
- **Output**:
    - A list of dictionaries representing the updated state of each document section, with keys 'order_idx', 'title', and 'content'.


---
#### AutoDocInitState._update_sections_with_pdf
The function `_update_sections_with_pdf` updates document sections based on content from a PDF file, using an LLM to generate new content for each section from each page of the PDF.
- **Inputs**:
    - `llm`: An instance of `ChatOpenAI`, representing the language model used to generate responses.
    - `previous_state`: A list of dictionaries, each containing the current state of a document section with keys 'order_idx', 'title', and 'content'.
    - `pdf_path`: A string representing the file path of the PDF being processed.
    - `pdf_pages`: A list of strings, each representing the content of a page from the PDF.
    - `pdf_annotations`: An optional list of `Category` enums indicating the relevance of each page to each section, or `None` if no annotations are provided.
- **Control Flow**:
    - The function begins by asserting that the length of `previous_state` matches the number of sections in `self.sections`.
    - A common update prompt is defined to be used in generating new content for each section.
    - The function initializes `temp_results` with the current content of each section from `previous_state`.
    - For each page in `pdf_pages`, the function constructs prompts for each section, combining the current section content, the common update prompt, and the page content.
    - An asynchronous task group is created to handle the generation of new content for each section using the LLM, conditioned on the relevance of the page and the section's creation method.
    - The results from the LLM tasks are collected and used to update `temp_results`.
    - After processing all pages, a new state is constructed by combining the updated content with the original order and title from `previous_state`.
- **Output**:
    - A list of dictionaries representing the updated state of each document section, with keys 'order_idx', 'title', and 'content'.


---
#### AutoDocInitState.assembly_system_prompt
The `assembly_system_prompt` function generates a system prompt template for assembling a final document draft by consolidating section content.
- **Inputs**:
    - None
- **Control Flow**:
    - Initialize a multi-line string `system_prompt_template` with placeholders for `goal`, `preamble_content`, and `sections`.
    - Initialize an empty string `sections`.
    - Iterate over `self.sections`, constructing a Markdown heading and appending section details to `sections`.
    - Construct `preamble_content` based on the presence of `self.scope.preamble`.
    - Return the formatted `system_prompt_template` with `goal`, `preamble_content`, and `sections` filled in.
- **Output**:
    - A formatted string representing the system prompt for document assembly.


---
#### AutoDocInitState.final_copy_editor_system_prompt
The `final_copy_editor_system_prompt` function generates a system prompt for a copy editor to finalize a document draft by ensuring proper Markdown formatting and coherence without altering the content.
- **Inputs**:
    - None
- **Control Flow**:
    - Initialize a template string `system_prompt_template` with instructions for the copy editor.
    - Construct a string `sections` by iterating over `self.sections`, formatting each section's title and level into Markdown headers.
    - Create a `preamble_content` string based on `self.scope.preamble`, adding context if it is not empty.
    - Return the formatted `system_prompt_template` with placeholders replaced by `self.document.goal`, `preamble_content`, and `sections`.
- **Output**:
    - A formatted string containing the system prompt for the copy editor.


---
#### AutoDocInitState.from_cfg
The `from_cfg` function asynchronously creates an instance of `AutoDocInitState` from a given configuration, execution mode, and optional page ID, and initializes sections based on the document format specified in the configuration.
- **Inputs**:
    - `cls`: The class `AutoDocInitState` which is being instantiated.
    - `cfg`: An instance of `AutoDocCfg` containing the configuration for the document generation process.
    - `execution_mode`: An instance of `ExecutionMode` indicating whether the process should run in LOCAL or MODAL mode.
    - `page_id`: An optional string representing the page ID, defaulting to an empty string.
- **Control Flow**:
    - Check if the `cfg.scope.preamble` is not empty and prepare `preamble_content` accordingly.
    - Print the document goal and configuration details.
    - Use a match-case statement to handle different document formats specified in `cfg.document.fmt`.
    - For `DocKind.DEFINED_SECTIONS`, determine targets and load driver documents based on the execution mode.
    - Build subgraphs and perform topological sorting on them.
    - Reverse the topological order and construct a user prompt from the document descriptions.
    - Split the user prompt into chunks if necessary and initialize a `ChatOpenAI` instance.
    - Evaluate optional sections using the `eval_optional_sections` method and return an instance of `AutoDocInitState`.
    - For `DocKind.UNDEFINED`, call `_autogen_sections` to generate sections and return an instance of `AutoDocInitState`.
    - Raise `NotImplementedError` for unsupported document formats.
- **Output**:
    - An instance of `AutoDocInitState` initialized with the specified configuration, document, scope, and sections.


---
#### AutoDocInitState.from_disk
The `from_disk` function reads a JSON file from a given path and returns an instance of the class initialized with the configuration data from the file.
- **Inputs**:
    - `cls`: The class type that the method is being called on, used to create an instance of the class.
    - `json_p`: A `Path` object representing the file path to the JSON file that contains the configuration data.
- **Control Flow**:
    - Open the file at the path specified by `json_p` for reading.
    - Load the JSON data from the file into a Python dictionary using `json.load`.
    - Extract the configuration data from the dictionary using the key `"cfg"`.
    - Return a new instance of the class `cls`, initialized with the configuration data using keyword arguments.
- **Output**:
    - An instance of the class `cls`, initialized with the configuration data from the JSON file.


---
#### AutoDocInitState.generate
The `generate` function orchestrates the process of generating a document by initializing, updating, and finalizing sections based on code and PDF content, using various language models for different stages of the document creation.
- **Inputs**:
    - `execution_mode`: Specifies the mode of execution, either 'LOCAL' or 'MODAL', which affects how resources like PDFs are accessed and processed.
    - `resume`: A boolean flag indicating whether to resume from a previously saved state or start a new document generation process.
    - `page_id`: An optional string identifier for the page, used when updating the status of the document generation process in 'MODAL' execution mode.
- **Control Flow**:
    - Initialize various language models for different stages of document generation, such as tagging, section initialization, updating, formatting, assembly, and copy editing.
    - If the execution mode is 'MODAL', download PDFs from S3 storage.
    - Convert any available PDFs to markdown format and store them in a dictionary.
    - If resuming, load the previous state, including revisions, initial state, and annotations, and set up the document generation context.
    - If not resuming, create path traversal state by building subgraphs and topological sorts of the codebase, and annotate nodes if tagging is enabled.
    - Generate initial section drafts using the initialized language models and save the initial state.
    - Iteratively update sections by processing each node in the reverse topological order, updating sections with content from code and PDFs, and saving the state after each update.
    - Perform a final formatting pass on the sections to ensure the output structure is correct.
    - Assemble the final document by combining all sections into a single cohesive document using the assembly language model.
    - Perform a final copy editing pass to polish the document and add a signature line.
    - Save the final document to a markdown file and return the final document content.
- **Output**:
    - The function returns the final document content as a string after all sections have been generated, updated, formatted, and assembled.


---
#### AutoDocInitState.load_annotations
The `load_annotations` function loads and returns the configuration and annotations from a JSON file based on the document's format and scope roots.
- **Inputs**:
    - `self`: An instance of a class that contains `scope` and `document` attributes, which are used to determine the filename for loading annotations.
- **Control Flow**:
    - The function calls `build_annotations_filename` with `scope_roots` and `fmt` to construct the filename for the annotations JSON file.
    - It opens the file with the constructed filename and loads its content as a JSON object into the `state` variable.
    - If `self.document.use_tagging` is `True`, it processes the `state['annotations']` to convert each annotation into a `Category` object, otherwise, it sets `annotations` to `None`.
    - It extracts the `cfg` from the `state` and initializes an `AutoDocInitState` object with it.
    - The function returns a tuple containing the `cfg_cls` (an `AutoDocInitState` object) and the `annotations`.
- **Output**:
    - A tuple containing an `AutoDocInitState` object and a dictionary of annotations, or `None` if tagging is not used.


---
#### AutoDocInitState.load_state
The `load_state` function loads and processes a saved state from a JSON file, transforming certain data structures for further use.
- **Inputs**:
    - `self`: An instance of the class containing the `load_state` method, which provides access to the class's attributes such as `scope` and `document`.
- **Control Flow**:
    - Builds the state filename using the `build_state_filename` function with `scope_roots` and `fmt` from the class instance.
    - Opens the file with the constructed filename and loads its JSON content into a variable `state`.
    - If `use_tagging` is enabled in the document configuration, it converts the `annotations` in `state['init_state']` to a dictionary of `Category` objects.
    - Transforms `appended_reverse_topo` in `state['init_state']` by validating each JSON entry into `TechDocsContent` objects.
    - Converts `init_node_set` in `state['init_state']` from a list to a set.
    - Returns the processed `state` dictionary.
- **Output**:
    - A dictionary representing the loaded and processed state, with specific transformations applied to its components.


---
#### AutoDocInitState.save_annotations
The `save_annotations` function saves annotation data and configuration to a JSON file.
- **Inputs**:
    - `self`: An instance of the class containing the `save_annotations` method, which includes attributes like `scope` and `document`.
    - `annotations`: A dictionary where keys are strings and values are lists of `Category` objects, representing annotations to be saved.
- **Control Flow**:
    - The function calls `build_annotations_filename` with `scope_roots` and `fmt` attributes from `self` to generate a filename for saving the annotations.
    - A dictionary `state` is created to store the `annotations` and the result of `self.model_dump()`, which presumably contains the current configuration or state of the object.
    - The function opens a file with the generated filename in write mode and writes the JSON-serialized `state` dictionary to it.
- **Output**:
    - The function does not return any value; it performs a side effect by writing data to a file.


---
#### AutoDocInitState.save_state
The `save_state` function saves the current state of a document generation process to a JSON file.
- **Inputs**:
    - `revisions`: A list of dictionaries representing the revisions made during the document generation process.
    - `init_state`: A dictionary representing the initial state of the document generation process, including information like appended reverse topology and initial node set.
    - `final_doc_revisions`: An optional list of strings representing the final document revisions, defaulting to None if not provided.
- **Control Flow**:
    - The function begins by building a filename for the state file using the `build_state_filename` function, which takes the scope roots and document format as parameters.
    - A deep copy of the `init_state` is created to avoid modifying the original input.
    - The `init_state` is updated by converting the 'appended_reverse_topo' list of tuples into a list of tuples where the second element is serialized to JSON, and the 'init_node_set' is converted to a list.
    - A new dictionary `state` is created to hold the `init_state`, `revisions`, and `cfg` (configuration) data.
    - If `final_doc_revisions` is provided, it is added to the `state` dictionary.
    - The `state` dictionary is serialized to a JSON string and written to a file with the name `state_filename`.
- **Output**:
    - The function does not return any value; it writes the state data to a file as a side effect.


---
#### AutoDocInitState.to_disk
The `to_disk` function writes the JSON representation of a `DriverDocsContent` object to a specified file path.
- **Inputs**:
    - `self`: An instance of the `DriverDocsContent` class, which contains the data to be serialized and written to disk.
    - `p`: A `Path` object representing the file path where the JSON data will be written.
- **Control Flow**:
    - The function calls `self.model_dump_json()` to get the JSON representation of the `DriverDocsContent` instance.
    - It opens the file at the specified path `p` in write mode.
    - It writes the JSON data to the file.
- **Output**:
    - The function does not return any value; it writes data to a file as a side effect.


---
#### AutoDocInitState.write_final_output_to_markdown
The `write_final_output_to_markdown` function writes a given string output to a markdown file with a specific filename format.
- **Inputs**:
    - `output`: A string containing the content to be written to the markdown file.
- **Control Flow**:
    - The function sets the format to 'document'.
    - It calls `build_state_filename` with the scope roots, format, and file extension '.md' to generate the filename.
    - It opens the generated filename in write mode.
    - It writes the provided output string to the file.
- **Output**:
    - The function does not return any value; it writes the output to a markdown file.



---
### Category 
- **Type**: `class`
- **Members**:
    - `HighlyRelevant`: Represents a category with a value of 0 indicating high relevance.
    - `SomewhatRelevant`: Represents a category with a value of 1 indicating moderate relevance.
    - `Irrelevant`: Represents a category with a value of 2 indicating no relevance.
- **Description**: The `Category` class is an enumeration that categorizes items into three levels of relevance: HighlyRelevant, SomewhatRelevant, and Irrelevant, each associated with an integer value. It provides a class method `from_str` to create a `Category` instance from a string representation of an integer.
- **Inherits From**:
    - IntEnum

**Methods**

---
#### Category.from_str
The `from_str` function converts a string representation of an integer to an instance of the class it belongs to.
- **Inputs**:
    - `cls`: The class to which the method belongs, typically passed automatically when called on a class.
    - `s`: A string representing an integer that will be converted to an instance of the class.
- **Control Flow**:
    - The function takes a string `s` as input.
    - It converts the string `s` to an integer using `int(s)`.
    - It returns an instance of the class `cls` initialized with the integer value.
- **Output**:
    - An instance of the class `cls` initialized with the integer value derived from the string `s`.



---
### DocKind 
- **Type**: `class`
- **Members**:
    - `DEFINED_SECTIONS`: Represents a document kind with defined sections.
    - `UNDEFINED`: Represents a document kind that is undefined.
    - `FROM_EXAMPLE`: Represents a document kind derived from an example.
    - `ARCHITECTURE`: Represents a document kind related to architecture.
- **Description**: The `DocKind` class is an enumeration that inherits from `StrEnum` and defines different kinds of document types. Each member of this enumeration represents a specific type of document categorization, such as 'defined_sections', 'undefined', 'from_example', and 'architecture'. This class is useful for categorizing documents based on their structure or origin.
- **Inherits From**:
    - StrEnum


---
### DocumentCfg 
- **Type**: `class`
- **Members**:
    - `goal`: A string representing the goal of the document configuration.
    - `fmt`: An instance of DocKind indicating the format of the document.
    - `use_tagging`: A boolean indicating whether tagging is used in the document configuration.
    - `config_name`: A string representing the name of the configuration.
    - `config_version`: A string representing the version of the configuration.
- **Description**: The `DocumentCfg` class is a configuration model for document generation, inheriting from `BaseModel`. It encapsulates the essential settings for creating a document, including the goal, format, and whether tagging is used. Additionally, it holds metadata about the configuration's name and version, facilitating the management and identification of different document configurations.
- **Inherits From**:
    - BaseModel


---
### DriverDocsContent 
- **Type**: `class`
- **Members**:
    - `codebase_name`: A string representing the name of the codebase.
    - `version_id`: A string representing the version identifier.
    - `dag`: A dictionary representing a directed acyclic graph with string keys and set of strings as values.
    - `content`: A dictionary mapping strings to TechDocsContent objects.
    - `topo_order`: A list of strings representing the topological order of the DAG.
- **Description**: The `DriverDocsContent` class is a data model that represents documentation content for a specific version of a codebase. It includes attributes for the codebase name, version ID, a directed acyclic graph (DAG) representing file dependencies, and a mapping of file paths to their respective `TechDocsContent`. The class provides methods to serialize and deserialize its data to and from disk, as well as to construct an instance from a database. Additionally, it offers a method to iterate over the content in topological order, facilitating operations that depend on the order of file dependencies.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### DriverDocsContent.from_db
The `from_db` function retrieves and constructs a `DriverDocsContent` object from a database using a specified version ID and relative path.
- **Inputs**:
    - `version_id`: A string representing the unique identifier of the version to retrieve from the database.
    - `relative_path`: A string representing the relative path to be used for retrieving derived contents.
- **Control Flow**:
    - Import necessary modules and functions for database interaction and ORM operations.
    - Establish a session with the database using `get_session()`.
    - Execute a query to retrieve the `Version` object matching the given `version_id`, including its primary asset using `selectinload`.
    - Extract `codebase_name`, `primary_asset_id`, and `organization_id` from the retrieved `Version` object.
    - Compute a `bucket` name by hashing the `organization_id`.
    - Retrieve derived contents for short sentence, long, and short paragraph descriptions using `_get_derived_contents` function for the given `version_id` and `relative_path`.
    - Create a temporary directory for downloading content from S3.
    - Attempt to construct a `content` dictionary by downloading source files from S3 and associating them with their descriptions.
    - If an exception occurs during content download, print the `codebase_name` and re-raise the exception.
    - Build a file tree DAG using `build_file_tree_dag` with the downloaded content and compute a topological sort of the DAG.
    - Return a `DriverDocsContent` object initialized with the retrieved and processed data.
- **Output**:
    - A `DriverDocsContent` object containing the codebase name, version ID, DAG, content dictionary, and topological order list.


---
#### DriverDocsContent.from_disk
The `from_disk` function reads a JSON file from a given path and validates it against a class model.
- **Inputs**:
    - `p`: A `Path` object representing the file path from which the JSON data will be read.
- **Control Flow**:
    - Open the file at the specified path `p` for reading.
    - Read the entire content of the file into a string `json_raw`.
    - Call the `model_validate_json` method of the class `cls` with `json_raw` to validate and return the model instance.
- **Output**:
    - An instance of the class `cls` that is validated against the JSON data read from the file.


---
#### DriverDocsContent.to_disk
The `to_disk` function serializes the `DriverDocsContent` object to JSON format and writes it to a specified file path.
- **Inputs**:
    - `p`: A `Path` object representing the file path where the JSON data will be written.
- **Control Flow**:
    - Call the `model_dump_json` method on the `DriverDocsContent` object to serialize it into a JSON string.
    - Open the file at the specified path `p` in write mode.
    - Write the JSON string to the file.
- **Output**:
    - The function does not return any value (returns `None`).


---
#### DriverDocsContent.walk_topo
The `walk_topo` function generates tuples of a string and `TechDocsContent` object in topological order.
- **Inputs**:
    - None
- **Control Flow**:
    - The function uses a generator expression to iterate over `self.topo_order`.
    - For each element `p` in `self.topo_order`, it yields a tuple consisting of `p` and `self.content[p]`.
- **Output**:
    - A generator that yields tuples, each containing a string and a `TechDocsContent` object, in the order specified by `self.topo_order`.



---
### ExecutionMode 
- **Type**: `class`
- **Members**:
    - `LOCAL`: Represents the local execution mode.
    - `MODAL`: Represents the modal execution mode.
- **Description**: The `ExecutionMode` class is an enumeration that defines two modes of execution: `LOCAL` and `MODAL`. It inherits from `StrEnum`, allowing the enumeration members to be strings. This class is used to specify the context or environment in which certain operations or processes should be executed, providing a clear distinction between local and modal execution contexts.
- **Inherits From**:
    - StrEnum


---
### FullyQualifiedDriverPathCode 
- **Type**: `class`
- **Members**:
    - `version_id`: A string representing the version identifier.
    - `node_path`: A string representing the path to a node.
- **Description**: The `FullyQualifiedDriverPathCode` class is a simple data model that inherits from `BaseModel` and is used to represent a fully qualified path to a driver code node, including its version identifier and node path. This class is part of a larger system that likely deals with managing and documenting code versions and paths.
- **Inherits From**:
    - BaseModel


---
### FullyQualifiedDriverPathPdf 
- **Type**: `class`
- **Members**:
    - `version_id`: A string representing the version identifier.
    - `pdf_name`: A string representing the name of the PDF file.
- **Description**: The `FullyQualifiedDriverPathPdf` class is a simple data model that inherits from `BaseModel` and is used to represent a fully qualified path to a PDF file associated with a specific version. It contains two attributes: `version_id`, which is a string identifier for the version, and `pdf_name`, which is a string representing the name of the PDF file. This class is likely used in contexts where PDF files need to be associated with specific versions of a document or software.
- **Inherits From**:
    - BaseModel


---
### LlmCfg 
- **Type**: `class`
- **Members**:
    - `tag_model`: A string representing the model used for tagging.
    - `section_init_model`: A string representing the model used for initializing sections.
    - `section_update_model`: A string representing the model used for updating sections.
    - `section_format_model`: A string representing the model used for formatting sections.
    - `assembly_model`: A string representing the model used for assembling documents.
    - `copy_editor_model`: A string representing the model used for copy editing.
- **Description**: The `LlmCfg` class is a configuration class that inherits from `BaseModel` and is used to define various language model configurations for different stages of document processing, such as tagging, section initialization, updating, formatting, assembly, and copy editing. It provides a class method `default` to return a default configuration with predefined model names for each stage.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### LlmCfg.default
The `default` function creates and returns an instance of the `LlmCfg` class with predefined model configurations.
- **Inputs**:
    - None
- **Control Flow**:
    - The function is a class method, indicated by the `cls` parameter, which refers to the class itself.
    - It returns an instance of the class `LlmCfg` with specific model configurations set for various attributes.
- **Output**:
    - An instance of the `LlmCfg` class with specific default model configurations for different attributes.



---
### NamedFlag 
- **Type**: `class`
- **Members**:
    - `index`: An integer representing the index of the flag.
    - `name`: A string representing the name of the flag.
    - `flag`: A boolean indicating the state of the flag.
- **Description**: The `NamedFlag` class is a simple data model that represents a flag with an associated index and name. It is used to encapsulate the concept of a flag, which can be either true or false, along with a unique identifier and a descriptive name. This class inherits from `BaseModel`, which suggests it is part of a system that uses Pydantic for data validation and management.
- **Inherits From**:
    - BaseModel


---
### Scope 
- **Type**: `class`
- **Members**:
    - `preamble`: A string representing the introductory text or context for the scope.
    - `pdfs`: A list of FullyQualifiedDriverPathPdf objects representing PDF paths associated with the scope.
    - `code`: A list of FullyQualifiedDriverPathCode objects representing code paths associated with the scope.
- **Description**: The `Scope` class is a data model that encapsulates a specific context or environment for a document generation process, including introductory text, associated PDF paths, and code paths. It provides a class method `default` to instantiate a `Scope` object with default values, which are empty strings and lists for its attributes. This class is used to define the boundaries and resources available for generating documentation.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### Scope.default
The `default` function creates and returns an instance of the class with default values for its attributes.
- **Inputs**:
    - None
- **Control Flow**:
    - The function is a class method, indicated by the `cls` parameter, which refers to the class itself.
    - It returns an instance of the class by calling `cls()` with specific default arguments.
    - The `preamble` attribute is set to an empty string, while `code` and `pdfs` are initialized as empty lists.
- **Output**:
    - An instance of the class with `preamble` as an empty string, and `code` and `pdfs` as empty lists.



---
### SectionCfg 
- **Type**: `class`
- **Members**:
    - `title`: The title of the section.
    - `level`: The hierarchical level of the section.
    - `required`: Indicates if the section is mandatory, default is True.
    - `instruction`: Instructions or guidelines for the section content.
    - `content_structure`: The structure or format of the section content.
    - `section_creation_method`: The method used to create the section, defined by SectionCreationMethod.
    - `committed_with`: Specifies another section with which this section is committed, default is None.
- **Description**: The `SectionCfg` class is a configuration model for defining sections within a document, specifying attributes such as title, level, and content structure. It includes options for whether a section is required and the method of its creation, allowing for flexible document configuration and generation.
- **Inherits From**:
    - BaseModel


---
### SectionCommitted 
- **Type**: `class`
- **Members**:
    - `title`: The title of the section.
    - `level`: The hierarchical level of the section.
    - `instruction`: Instructions or description for the section.
    - `content_structure`: The structure format for the section content.
    - `section_creation_method`: The method used to create the section.
- **Description**: The `SectionCommitted` class is a data model that represents a committed section of a document, encapsulating its title, level, instructions, content structure, and creation method. It provides various methods to generate system prompts for different document processing tasks, such as annotation, drafting, updating, and final formatting, tailored to the specific needs of the section. These methods facilitate the integration of the section into larger document workflows, ensuring that the section is relevant, well-structured, and formatted according to the specified guidelines.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### SectionCommitted.aggregate_aggregate_sections
The function `aggregate_aggregate_sections` asynchronously aggregates multiple document sections into a single list of aggregated documents using a language model.
- **Inputs**:
    - `goal`: A string representing the goal of the document being written.
    - `preamble`: A string providing additional context or introduction for the document.
    - `aggregate_docs`: A list of document sections that need to be aggregated.
    - `section_name`: A string representing the name of the section being aggregated.
- **Control Flow**:
    - Initialize a language model `llm` with specific parameters.
    - Construct user prompts for each document section using `gather_aggregate_user_prompt_constructor`.
    - Create a list of coroutines for generating responses from the language model for each user prompt.
    - Print a message indicating the aggregation process and the number of coroutines.
    - Use `asyncio.gather` to execute all coroutines concurrently and collect their responses.
    - Append each response to `new_aggregate_docs`.
    - Return the list `new_aggregate_docs` containing the aggregated document sections.
- **Output**:
    - A list of strings, each representing an aggregated document section.


---
#### SectionCommitted.aggregate_node_sections
The `aggregate_node_sections` function asynchronously aggregates content from multiple node sections into a list of documents using a language model.
- **Inputs**:
    - `goal`: A string representing the goal of the document being written.
    - `preamble`: A string providing additional context or introduction for the document.
    - `file_by_file_content`: A dictionary where keys are file or folder identifiers and values are the content associated with each.
    - `section_name`: A string representing the name of the section being aggregated.
- **Control Flow**:
    - Initialize a language model `llm` with specific parameters.
    - Call `gather_user_prompt_constructor` to create user prompts based on `file_by_file_content` and `section_name`.
    - Iterate over each user prompt and append a coroutine to `aggregate_coroutines` for generating a response using `llm_generate`.
    - Print the number of coroutines being aggregated for the given `section_name`.
    - Use `asyncio.gather` to execute all coroutines concurrently and collect their responses.
    - Append each response to `aggregate_docs`.
    - Return the list `aggregate_docs` containing all aggregated document sections.
- **Output**:
    - A list of aggregated document sections, each generated from the content of the input nodes.


---
#### SectionCommitted.annotation_system_prompt
The `annotation_system_prompt` function generates a system prompt for annotating code files and folders based on their relevance to a specific document section.
- **Inputs**:
    - `goal`: A string representing the goal of the specific document being written.
    - `preamble`: A string providing additional context or preamble for the document, which can be empty.
- **Control Flow**:
    - A template string `system_prompt_template` is defined, which outlines the role of the annotator and the categories for relevance assessment.
    - The `preamble_content` is conditionally constructed based on whether the `preamble` input is non-empty.
    - The `heading` is determined by the `level` attribute of the class instance, represented by a series of hash symbols.
    - The `system_prompt_template` is formatted with the provided `goal`, `preamble_content`, `heading`, `title`, and `instruction` attributes of the class instance.
    - The formatted string is returned as the output.
- **Output**:
    - A formatted string that serves as a system prompt for annotating code files and folders.


---
#### SectionCommitted.code_example_few_shot_generator
The `code_example_few_shot_generator` function generates code examples for a document section using a few-shot learning approach with an LLM, potentially aggregating multiple examples into a coherent single example.
- **Inputs**:
    - `document_goal`: A string representing the goal of the document for which code examples are being generated.
    - `document_preamble`: A string containing the preamble or introductory content of the document.
    - `reverse_topos`: A list of reverse topological orderings of nodes, where each node is a tuple containing a path and its associated `TechDocsContent`.
    - `tagged_nodes`: An optional dictionary mapping node paths to lists of `Category` objects, indicating the relevance of each node to the document sections.
    - `tag_idx`: An optional integer index used to select a specific tag from the `tagged_nodes` for filtering relevant nodes.
- **Control Flow**:
    - Initialize a ChatOpenAI instance with specific model parameters.
    - Construct user prompts for source code aggregation using the `source_code_aggregation_user_prompt_constructor` method.
    - Create a list of coroutines for generating code examples using the `llm_generate` function for each user prompt.
    - Await the completion of all coroutines using `asyncio.gather` to get responses.
    - If multiple responses are received, aggregate them into a single coherent example using another LLM call.
    - Return the single aggregated response or the first response if only one was generated.
- **Output**:
    - The function returns a string containing the generated code example, which may be a single example or an aggregated one from multiple examples.


---
#### SectionCommitted.code_example_single_pass_aggregate_pass
The function `code_example_single_pass_aggregate_pass` generates a markdown-formatted draft of a code example by combining multiple code examples into a coherent example for a specific document section.
- **Inputs**:
    - `goal`: A string representing the goal of the document for which the code example is being written.
    - `preamble`: A string providing additional context or preamble for the document, which can be empty.
- **Control Flow**:
    - A template string `system_prompt_template` is defined to guide the generation of the code example draft.
    - The `preamble_content` is conditionally constructed based on whether the `preamble` is empty or not.
    - The `heading` is determined by the level attribute of the class instance (`self.level`).
    - The `system_prompt_template` is formatted with the provided `goal`, `preamble_content`, `heading`, `title`, `instruction`, and `content_structure` attributes of the class instance.
    - The formatted string is returned as the output.
- **Output**:
    - A formatted string that serves as a system prompt for generating a markdown-formatted code example draft.


---
#### SectionCommitted.code_example_single_pass_system_prompt
The function generates a system prompt for drafting a code example based on provided goals and preamble.
- **Inputs**:
    - `goal`: A string representing the goal of the document or section being written.
    - `preamble`: A string providing additional context or introductory information for the document or section.
- **Control Flow**:
    - A template string for the system prompt is defined, which includes placeholders for various components such as goal, preamble content, title, heading, instruction, and content structure.
    - The preamble content is conditionally constructed based on whether the preamble string is empty or not.
    - The heading level is determined by the 'level' attribute of the class instance.
    - The template string is formatted with the provided goal, constructed preamble content, heading, title, instruction, and content structure, and the formatted string is returned.
- **Output**:
    - A formatted string representing the system prompt for drafting a code example, with markdown formatting instructions.


---
#### SectionCommitted.create_node_sections
The `create_node_sections` function generates content sections for nodes and PDF pages using a language model based on their relevance to a specified goal and preamble.
- **Inputs**:
    - `goal`: A string representing the goal or objective for generating the node sections.
    - `preamble`: A string that provides additional context or introduction for the node sections.
    - `reverse_topos`: A list of lists, where each sublist contains tuples representing nodes and their content in reverse topological order.
    - `pdf_pages_dict`: An optional dictionary mapping PDF file paths to lists of strings, where each string represents the content of a page in the PDF.
    - `tagged_nodes`: An optional dictionary mapping node identifiers to lists of categories indicating their relevance.
    - `pdf_tagged_nodes`: An optional dictionary mapping PDF file paths to dictionaries, which map page indices to lists of categories indicating their relevance.
    - `tag_idx`: An optional integer index used to access specific tags in the tagged_nodes and pdf_tagged_nodes dictionaries.
- **Control Flow**:
    - Initialize a language model with a specified model and settings.
    - Create empty dictionaries and lists to store content and coroutines for node processing.
    - Iterate over each reverse topological order list in reverse_topos.
    - For each node in the list, construct a user prompt and add a coroutine to generate content using the language model if the node is relevant.
    - Iterate over each PDF path in pdf_pages_dict and for each page, construct a user prompt and add a coroutine to generate content if the page is relevant.
    - Execute all coroutines concurrently using asyncio.gather to generate content for each node and PDF page.
    - Store the generated content in a dictionary mapping node identifiers to their respective content.
    - Return the dictionary containing the generated content for all nodes and PDF pages.
- **Output**:
    - A dictionary mapping node identifiers and PDF page identifiers to their generated content sections.


---
#### SectionCommitted.create_section_scatter_gather
The `create_section_scatter_gather` function asynchronously creates and aggregates document sections based on provided content and configuration.
- **Inputs**:
    - `self`: The instance of the class where this method is defined.
    - `goal`: A string representing the goal of the document being created.
    - `preamble`: A string containing the preamble or introductory content for the document.
    - `reverse_topos`: A list of topologically sorted nodes in reverse order, representing the structure of the document.
    - `pdf_pages_dict`: An optional dictionary mapping PDF file paths to lists of their page contents.
    - `tagged_nodes`: An optional dictionary containing nodes tagged with relevance categories.
    - `pdf_tagged_nodes`: An optional dictionary containing PDF pages tagged with relevance categories.
    - `tag_idx`: An optional integer index used for tagging.
    - `section_name`: A string representing the name of the section being created.
- **Control Flow**:
    - Prints a message indicating the start of section creation for the given section name.
    - Calls `create_node_sections` to generate content for each node based on the provided parameters.
    - Calls `aggregate_node_sections` to combine the generated node content into aggregate documents.
    - Enters a loop to further aggregate the documents until only one document remains.
    - Returns the final aggregated document.
- **Output**:
    - Returns a single string representing the final aggregated document section.


---
#### SectionCommitted.final_output_format
The `final_output_format` function generates a formatted system prompt for writing the final form of a document section using Markdown syntax, based on a given goal and preamble.
- **Inputs**:
    - `goal`: A string representing the goal of the document section to be written.
    - `preamble`: A string providing additional context or preamble for the document section.
- **Control Flow**:
    - The function defines a template string `system_prompt_template` that outlines the structure and content of the final document section.
    - It checks if the `preamble` is not empty and constructs `preamble_content` accordingly.
    - It calculates the Markdown heading level using the `self.level` attribute.
    - The function returns the formatted system prompt by substituting placeholders in the template with the provided `goal`, `preamble_content`, `heading`, `self.title`, and `self.content_structure`.
- **Output**:
    - A formatted string representing the system prompt for writing the final document section.


---
#### SectionCommitted.from_section_cfg
The `from_section_cfg` function creates an instance of the `SectionCommitted` class from a given `SectionCfg` configuration object.
- **Inputs**:
    - `cfg`: An instance of the `SectionCfg` class containing configuration details for a section, including title, level, instruction, content structure, and section creation method.
- **Control Flow**:
    - The function takes a `SectionCfg` object as input.
    - It returns a new instance of the `SectionCommitted` class.
    - The new instance is initialized with the properties of the `SectionCfg` object, specifically `title`, `level`, `instruction`, `content_structure`, and `section_creation_method`.
- **Output**:
    - An instance of the `SectionCommitted` class initialized with the properties from the provided `SectionCfg` object.


---
#### SectionCommitted.gather_aggregate_user_prompt_constructor
The function `gather_aggregate_user_prompt_constructor` constructs a list of user prompts by aggregating document content with section names.
- **Inputs**:
    - `self`: Refers to the instance of the class in which this method is defined.
    - `aggregate_docs`: A list of document contents that need to be aggregated into user prompts.
    - `section_name`: A string representing the name of the section to be included in the user prompts.
- **Control Flow**:
    - Initialize a list `user_prompts` with an empty string as its first element.
    - Iterate over the `aggregate_docs` list with an index `idx` and document `doc`.
    - For each document, append a formatted string containing the `section_name`, the index `idx`, and the document content `doc` to the first element of `user_prompts`.
    - Return the `user_prompts` list.
- **Output**:
    - Returns a list containing a single string, which is a concatenation of section names and document contents.


---
#### SectionCommitted.gather_multiple_system_prompt
The `gather_multiple_system_prompt` function generates a formatted system prompt for aggregating information from multiple document sections related to a specific goal and preamble.
- **Inputs**:
    - `goal`: A string representing the goal of the document being written.
    - `preamble`: A string providing additional context or introduction for the document.
- **Control Flow**:
    - The function defines a template string `aggregate_system_prompt_template` for the system prompt, which includes placeholders for various document components such as goal, preamble, title, heading, and instruction.
    - It checks if the `preamble` is not empty and constructs `preamble_content` accordingly, adding additional context if necessary.
    - The function calculates the heading level using the `self.level` attribute and assigns it to the `heading` variable.
    - Finally, it formats the `aggregate_system_prompt_template` with the provided `goal`, `preamble_content`, `heading`, `self.title`, and `self.instruction`, and returns the formatted string.
- **Output**:
    - The function returns a formatted string that serves as a system prompt for aggregating document sections.


---
#### SectionCommitted.gather_system_prompt
The `gather_system_prompt` function generates a formatted system prompt for aggregating document sections based on a given goal and preamble.
- **Inputs**:
    - `goal`: A string representing the goal of the document being written.
    - `preamble`: A string providing additional context or preamble for the document, which can be empty.
- **Control Flow**:
    - The function defines a template string `aggregate_system_prompt_template` for the system prompt, which includes placeholders for various document components.
    - It checks if the `preamble` is not empty and constructs `preamble_content` accordingly, adding additional context if needed.
    - The function calculates the heading level using the `self.level` attribute, represented by a string of hash symbols.
    - Finally, it formats the `aggregate_system_prompt_template` with the provided `goal`, `preamble_content`, `heading`, `self.title`, and `self.instruction`, and returns the formatted string.
- **Output**:
    - The function returns a formatted string that serves as a system prompt for aggregating document sections.


---
#### SectionCommitted.gather_user_prompt_constructor
The `gather_user_prompt_constructor` function constructs a list of user prompts by aggregating content from multiple files or folders, ensuring the prompts fit within a specified token limit.
- **Inputs**:
    - `self`: The instance of the class to which this method belongs.
    - `file_by_file_content`: A dictionary where keys are file or folder paths and values are their respective content.
    - `section_name`: A string representing the name of the section to be included in the user prompt.
- **Control Flow**:
    - Initialize variables for chunk size, overlap, and user prompts.
    - Iterate over each file or folder in `file_by_file_content`, appending its content to a single user prompt string.
    - Use `split_text` to determine if the user prompt needs to be split into multiple chunks based on the token limit.
    - If multiple chunks are required, calculate a token threshold and attempt to distribute content across multiple prompts without exceeding the threshold.
    - If a new prompt is needed, append it to the list of user prompts.
    - Return the list of constructed user prompts.
- **Output**:
    - A list of strings, each representing a user prompt constructed from the input content.


---
#### SectionCommitted.init_draft_system_prompt_code
The `init_draft_system_prompt_code` function generates a system prompt template for drafting a section of a document based on a given goal and preamble.
- **Inputs**:
    - `goal`: A string representing the goal of the document or section being drafted.
    - `preamble`: A string providing additional context or introductory information for the document or section.
- **Control Flow**:
    - A template string `system_prompt_template` is defined with placeholders for various components of the document.
    - The `preamble_content` is conditionally constructed based on whether the `preamble` is non-empty, adding additional context if applicable.
    - The `heading` is determined by the level attribute of the class instance, represented by a series of '#' characters.
    - The `system_prompt_template` is formatted with the provided `goal`, `preamble_content`, `heading`, `title`, and `instruction` attributes of the class instance.
    - The formatted string is returned as the output.
- **Output**:
    - A formatted string representing the system prompt for drafting a document section, with placeholders filled in based on the provided inputs and class attributes.


---
#### SectionCommitted.init_draft_system_prompt_pdf
The `init_draft_system_prompt_pdf` function generates a system prompt template for drafting a document section based on PDF content, using specified goals and preambles.
- **Inputs**:
    - `goal`: A string representing the goal of the document being drafted.
    - `preamble`: A string providing additional context or introduction for the document.
- **Control Flow**:
    - A template string `system_prompt_template` is defined with placeholders for various document components.
    - The `preamble_content` is conditionally constructed based on whether the `preamble` is non-empty, adding additional context if applicable.
    - The `heading` is determined by the level of the section, represented by a number of hash symbols corresponding to the section's level.
    - The function returns the formatted `system_prompt_template` with placeholders replaced by the provided `goal`, `preamble_content`, `heading`, and other attributes from the class instance.
- **Output**:
    - A formatted string representing the system prompt for drafting a document section, with markdown formatting instructions.


---
#### SectionCommitted.pdf_annotation_system_prompt
The `pdf_annotation_system_prompt` function generates a system prompt for annotating PDF pages based on their relevance to a specific document section.
- **Inputs**:
    - `goal`: A string representing the goal of the document being written.
    - `preamble`: A string providing additional context or preamble for the document.
- **Control Flow**:
    - The function defines a template string `system_prompt_template` that outlines the task of categorizing PDF pages based on their relevance to a document section.
    - It checks if the `preamble` is not empty and constructs `preamble_content` accordingly.
    - It determines the heading level using the `self.level` attribute.
    - The function formats the `system_prompt_template` with the provided `goal`, `preamble_content`, `heading`, `self.title`, and `self.instruction` to create the final system prompt.
- **Output**:
    - A formatted string that serves as a system prompt for annotating PDF pages.


---
#### SectionCommitted.scatter_system_prompt
The `scatter_system_prompt` function generates a system prompt for writing a document section based on a specific goal and preamble, formatted with markdown and technical details.
- **Inputs**:
    - `goal`: A string representing the goal of the document section to be written.
    - `preamble`: A string providing additional context or preamble for the document section.
- **Control Flow**:
    - The function defines a template string `system_prompt_template` that outlines the structure and content of the system prompt.
    - It checks if the `preamble` is not empty and constructs `preamble_content` accordingly.
    - It determines the heading level using the `self.level` attribute.
    - The function returns a formatted string by substituting placeholders in `system_prompt_template` with the provided `goal`, `preamble_content`, `heading`, `self.title`, and `self.instruction`.
- **Output**:
    - The function returns a formatted string that serves as a system prompt for writing a document section.


---
#### SectionCommitted.scatter_user_prompt_constructor
The `scatter_user_prompt_constructor` function constructs a user prompt string by combining descriptions and source code of a codebase node and its root.
- **Inputs**:
    - `root_content`: An instance of `TechDocsContent` representing the root content of the codebase, containing descriptions and possibly source code.
    - `node_content`: An instance of `TechDocsContent` representing the specific node content within the codebase, containing descriptions and possibly source code.
    - `node_path`: A string representing the path to the specific node within the codebase.
- **Control Flow**:
    - Initialize `user_prompt` with a short description of the full codebase from `root_content`.
    - Append a detailed description of the node specified by `node_path` from `node_content`.
    - Check if `node_content` has non-empty source code; if so, append it to `user_prompt`, otherwise indicate the file is empty.
    - Split the `user_prompt` into chunks if it exceeds a certain size, using the `split_text` function.
    - Return the first chunk if multiple chunks are created, otherwise return the complete `user_prompt`.
- **Output**:
    - A string representing the constructed user prompt, potentially truncated if it exceeds a certain size.


---
#### SectionCommitted.source_code_aggregation_user_prompt_constructor
The function constructs user prompts by aggregating source code from a list of reverse topological orders, considering annotations and chunk size constraints.
- **Inputs**:
    - `reverse_topos`: A list of reverse topological orders, where each element is a list of tuples containing a file path and its associated technical documentation.
    - `annotations`: A dictionary mapping file paths to lists of Category annotations, indicating the relevance of each file for a specific tag index, or None if not provided.
    - `tag_idx`: An optional integer representing the index of the tag to be considered when filtering files based on their annotations.
    - `chunk_size`: An integer specifying the maximum size of each chunk of text in the user prompt, defaulting to 100,000 characters.
- **Control Flow**:
    - Initialize an empty string 'user_prompt'.
    - Iterate over each reverse topological order in 'reverse_topos'.
    - For each file path and technical documentation pair, check if the file should be included based on 'tag_idx', 'annotations', and the presence of source code.
    - If the file is included, append its source code to 'user_prompt'.
    - Split 'user_prompt' into chunks based on 'chunk_size' using 'split_text'.
    - If multiple chunks are required, calculate a token threshold and distribute source code across multiple prompts to stay within the threshold.
    - Return a list of user prompts, either a single prompt or multiple prompts if chunking was necessary.
- **Output**:
    - A list of user prompts, each containing aggregated source code from the input files, split into chunks if necessary.


---
#### SectionCommitted.update_from_file_system_prompt
The `update_from_file_system_prompt` function generates a system prompt for updating a document section based on a specific file's content, using a given goal and preamble.
- **Inputs**:
    - `goal`: A string representing the goal of the document or section being updated.
    - `preamble`: A string providing additional context or introduction for the document or section.
- **Control Flow**:
    - A template string `system_prompt_template` is defined, which outlines the task of updating a document section based on a file's content.
    - The `preamble_content` is constructed by checking if the `preamble` is not empty and appending it to a formatted string.
    - The `heading` is determined by the level of the section, represented by the number of '#' characters.
    - The `system_prompt_template` is formatted with the provided `goal`, `preamble_content`, `heading`, `title`, and `instruction` attributes of the class instance.
    - The formatted system prompt is returned as the output.
- **Output**:
    - A formatted string representing the system prompt for updating a document section based on a file's content.


---
#### SectionCommitted.update_from_folder_system_prompt
The `update_from_folder_system_prompt` function generates a system prompt for updating a document section based on folder content summaries, focusing on high-level organization rather than technical details.
- **Inputs**:
    - `goal`: A string representing the goal of the document being written.
    - `preamble`: A string providing additional context or introduction for the document, which can be empty.
- **Control Flow**:
    - Define a template string `system_prompt_template` for the system prompt, which includes placeholders for various document details.
    - Check if the `preamble` is not empty; if so, format it into `preamble_content` with additional context text.
    - Determine the heading level using the `self.level` attribute and store it in `heading`.
    - Format the `system_prompt_template` with the provided `goal`, `preamble_content`, `heading`, `self.title`, and `self.instruction`.
    - Return the formatted system prompt string.
- **Output**:
    - A formatted string representing the system prompt for updating a document section based on folder content.


---
#### SectionCommitted.update_from_pdf_system_prompt
The `update_from_pdf_system_prompt` function generates a system prompt for updating a document section based on a PDF page, using a specified goal and preamble.
- **Inputs**:
    - `goal`: A string representing the goal of the document or section being updated.
    - `preamble`: A string providing additional context or introductory information for the document or section.
- **Control Flow**:
    - Define a template string `system_prompt_template` that outlines the task of updating a document section based on a PDF page.
    - Construct `preamble_content` by checking if the `preamble` is non-empty and formatting it accordingly.
    - Determine the heading level using the `self.level` attribute and store it in `heading`.
    - Format the `system_prompt_template` with the provided `goal`, `preamble_content`, `heading`, `self.title`, and `self.instruction`.
    - Return the formatted system prompt as a string.
- **Output**:
    - A formatted string representing the system prompt for updating a document section based on a PDF page.



---
### SectionCreationMethod 
- **Type**: `class`
- **Members**:
    - `SEQUENTIAL_EDIT`: Represents a section creation method where sections are edited sequentially.
    - `SCATTER_GATHER`: Represents a section creation method where sections are created by gathering information from scattered sources.
    - `ONLY_PDFS`: Represents a section creation method that uses only PDF documents.
    - `CODE_EXAMPLE`: Represents a section creation method that involves creating code examples.
- **Description**: The `SectionCreationMethod` class is an enumeration that defines different methods for creating sections in a document. It inherits from `StrEnum`, allowing each method to be represented as a string. The class provides four distinct methods: `SEQUENTIAL_EDIT`, `SCATTER_GATHER`, `ONLY_PDFS`, and `CODE_EXAMPLE`, each representing a different strategy for section creation in a documentation process.
- **Inherits From**:
    - StrEnum


---
### SectionFlags 
- **Type**: `class`
- **Members**:
    - `sections`: A list of NamedFlag objects representing different sections.
- **Description**: The SectionFlags class is a subclass of BaseModel and is designed to manage a collection of sections, each represented by a NamedFlag object. It provides a class method, from_llm, which asynchronously generates a list of relevant sections based on input from a language model (llm), a goal, a preamble, optional sections, and long descriptions. This method constructs a system prompt to guide the language model in determining the relevance of each section, and returns a validated model instance with the results.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### SectionFlags.from_llm
The `from_llm` function generates a validated model instance by using a language model to determine the relevance of optional sections for a document based on provided descriptions and goals.
- **Inputs**:
    - `cls`: The class type that the method is a part of, used to call class methods like `model_validate_json`.
    - `llm`: An instance of `ChatOpenAI`, representing the language model used to generate responses.
    - `goal`: A string describing the goal of the document being written.
    - `preamble`: A string providing additional context or introduction for the document.
    - `optional_sections`: A list of tuples, each containing a section index, section name, and section description, representing optional sections to be evaluated for inclusion.
    - `long_descriptions`: A string containing long descriptions of files and folders associated with the code, used as context for deciding the relevance of optional sections.
- **Control Flow**:
    - A system prompt template is defined to instruct the language model on how to evaluate the relevance of optional sections based on the provided goal, preamble, and section descriptions.
    - A user prompt is constructed using the long descriptions to provide context for the language model's decision-making process.
    - The preamble content is conditionally appended to the system prompt if it is not empty.
    - The optional section descriptions are formatted and appended to the system prompt.
    - The system prompt is formatted with the goal, preamble content, and optional section descriptions.
    - The language model is used to generate a response based on the system and user prompts, with the output configured to be a strict JSON format.
    - The generated response is validated and returned as a model instance using the class method `model_validate_json`.
- **Output**:
    - A validated model instance of the class `cls`, containing decisions on the relevance of optional sections as determined by the language model.



---
### TechDocsContent 
- **Type**: `class`
- **Members**:
    - `name`: The name of the technical document content.
    - `source`: The source of the content, which can be a string or None.
    - `short_sentence_description`: A brief description of the content in a single sentence.
    - `long_description`: A detailed description of the content.
    - `short_paragraph_description`: A concise paragraph describing the content.
- **Description**: The `TechDocsContent` class is a data model that represents the content of a technical document. It includes attributes for the name of the content, its source, and various levels of description, ranging from a short sentence to a long detailed description. This class is useful for organizing and managing different pieces of content within a technical documentation system.
- **Inherits From**:
    - BaseModel


# Functions

---
### _autogen_sections 
The function `_autogen_sections` is intended to automatically generate a list of `SectionCfg` objects based on an `AutoDocCfg` configuration.
- **Inputs**:
    - `cfg`: An instance of `AutoDocCfg` which contains configuration details for generating documentation sections.
- **Control Flow**:
    - The function is defined but not yet implemented, as indicated by the `raise NotImplementedError("TODO")` statement.
    - The function is expected to take an `AutoDocCfg` object as input and return a list of `SectionCfg` objects, but the logic for this is not yet provided.
- **Output**:
    - The function is supposed to return a list of `SectionCfg` objects, but currently, it raises a `NotImplementedError`.


---
### _download_pdf_from_s3 
The function `_download_pdf_from_s3` downloads a PDF file from an S3 bucket using metadata from a database.
- **Inputs**:
    - `version_id`: A string representing the unique identifier of the version for which the PDF is to be downloaded.
- **Control Flow**:
    - Import necessary modules and functions for database access and S3 interaction.
    - Establish a session with the database using `get_session()`.
    - Query the `Version` table to retrieve the version object associated with the given `version_id`, including its primary asset details.
    - Extract the `primary_asset_id`, `pdf_name`, and `organization_id` from the version's primary asset.
    - Query the `Node` table to retrieve the node object associated with the given `version_id`.
    - Compute the S3 bucket name by hashing the `organization_id` and taking the first 63 characters of the hash.
    - Ensure the local download directory exists by creating it if necessary.
    - Construct the local file path for the PDF using the `pdf_name`.
    - Initialize an S3 client using `boto3.client('s3')`.
    - Construct the S3 download key using `primary_asset_id`, `version_id`, and the node's `relative_path`.
    - Download the file from the S3 bucket to the local path using `s3_client.download_file()`.
- **Output**:
    - The function does not return any value; it performs a side effect by downloading a file to the local filesystem.


---
### _get_codebase_name 
The function `_get_codebase_name` extracts the first non-separator component of a given file path to construct a codebase name.
- **Inputs**:
    - `path`: A string representing the file path from which the codebase name is to be extracted.
- **Control Flow**:
    - Iterate over each part of the path using `Path(path).parts`.
    - Check if the current part is not equal to the OS-specific path separator `os.sep`.
    - If a part is found that is not a separator, return it as the codebase name.
    - If no valid part is found, raise a `ValueError` indicating that a codebase name could not be constructed.
- **Output**:
    - Returns the first non-separator component of the path as a string, or raises a `ValueError` if no such component is found.


---
### _get_derived_contents 
The function `_get_derived_contents` retrieves derived content from a database based on specified version ID, relative path, and content kind.
- **Inputs**:
    - `version_id`: A string representing the version ID of the node to filter the derived content.
    - `relative_path`: A string representing the relative path to filter the derived content, using a prefix match.
    - `dc_kind`: An instance of `ContentKind` enum specifying the kind of derived content to retrieve.
- **Control Flow**:
    - Import necessary modules and functions from the database and SQLModel libraries.
    - Establish a session with the database using `get_session()`.
    - Construct a SQL query using `select` to retrieve `DerivedContent` records that join with `Node` records, filtering by `version_id`, `relative_path` (using a prefix match), and `dc_kind`.
    - Execute the query using the session and retrieve all matching records.
    - Return a dictionary mapping each `DerivedContent`'s `relative_path` to its `content`.
- **Output**:
    - A dictionary mapping relative paths to their corresponding derived content as strings.


---
### _get_path_on_disk 
The function `_get_path_on_disk` constructs a file path for a JSON file associated with a given codebase name using a predefined local file path.
- **Inputs**:
    - `codebase_name`: A string representing the name of the codebase for which the file path is to be constructed.
- **Control Flow**:
    - Retrieve the absolute path of the root location for the given `codebase_name` from the `LOCAL_FILES` dictionary.
    - Construct a `Path` object by appending the codebase name with a `.json` extension to the retrieved root location path.
- **Output**:
    - A `Path` object representing the full path to the JSON file on disk for the specified codebase.


---
### _get_pdf_paths 
The `_get_pdf_paths` function generates a list of file paths for PDF files based on the execution mode and provided PDF names.
- **Inputs**:
    - `pdf_names`: A list of strings representing the names of the PDF files for which paths need to be generated.
    - `execution_mode`: An instance of the `ExecutionMode` enum indicating the mode of execution, which can be either `LOCAL` or `MODAL`.
- **Control Flow**:
    - The function uses a `match` statement to determine the execution mode.
    - If the execution mode is `ExecutionMode.LOCAL`, it constructs paths by combining the local root directory path from `LOCAL_FILES` with each PDF name.
    - If the execution mode is `ExecutionMode.MODAL`, it constructs paths by combining the `PDF_DOWNLOAD_DIR` with each PDF name.
    - The constructed list of paths is stored in the `pdf_paths` variable.
    - The function returns the `pdf_paths` list.
- **Output**:
    - A list of `Path` objects representing the file paths for the specified PDF files, constructed according to the execution mode.


---
### _get_source_from_s3 
The function `_get_source_from_s3` downloads a file from an S3 bucket and returns its content as a string.
- **Inputs**:
    - `version_id`: A string representing the version identifier of the asset to be downloaded.
    - `primary_asset_id`: A string representing the primary asset identifier, used to construct the S3 key for the file.
    - `relative_path`: A string representing the relative path of the file within the asset's directory structure.
    - `bucket`: A string representing the name of the S3 bucket from which the file will be downloaded.
    - `download_dir`: A string representing the local directory path where the file will be downloaded.
- **Control Flow**:
    - The function attempts to create an S3 client using `boto3.client('s3')`.
    - It constructs the S3 key for the file using the `primary_asset_id`, `version_id`, and `relative_path`.
    - It determines the local download path by combining `download_dir` and `relative_path`, ensuring the parent directories exist.
    - The function prints the bucket name and download key for debugging purposes.
    - It downloads the file from the specified S3 bucket to the local path using `s3_client.download_file`.
    - The function attempts to open the downloaded file and read its content, returning it as a string.
    - If any exception occurs during the process, the function returns `None`.
- **Output**:
    - The function returns the content of the downloaded file as a string, or `None` if an exception occurs.


---
### _get_target_name 
The function `_get_target_name` extracts and returns the name of the file or directory from a given file path.
- **Inputs**:
    - `path`: A string representing the file path from which the target name is to be extracted.
- **Control Flow**:
    - The function takes a single input, `path`, which is a string representing a file path.
    - It uses the `Path` class from the `pathlib` module to create a `Path` object from the input string.
    - The `name` attribute of the `Path` object is accessed, which provides the final component of the path, typically the file or directory name.
    - The function returns this name as a string.
- **Output**:
    - The function returns a string that is the name of the file or directory at the end of the given path.


---
### build_annotations_filename 
The `build_annotations_filename` function constructs a filename for annotations based on a list of code paths, a format string, and an optional file extension.
- **Inputs**:
    - `scope_roots`: A list of `FullyQualifiedDriverPathCode` objects, each containing a version ID and a node path, representing the root paths of the code scope.
    - `fmt`: A string representing the format of the annotations, used as part of the filename.
    - `ext`: An optional string representing the file extension, defaulting to ".json".
- **Control Flow**:
    - Extracts the codebase names from the `node_path` of each `FullyQualifiedDriverPathCode` in `scope_roots` using the `_get_codebase_name` function.
    - Removes duplicate codebase names while preserving order by converting the list to a dictionary and back to a list.
    - Limits the list of unique codebase names to the first three elements.
    - Joins the selected codebase names with underscores to form the base of the filename.
    - Constructs the final filename by appending the format string, "_annotations", and the file extension to the base name.
- **Output**:
    - A string representing the constructed filename for annotations, formatted as "<codebase_names>_<fmt>_annotations<ext>".


---
### build_file_tree_dag 
The `build_file_tree_dag` function constructs a directed acyclic graph (DAG) representing the file tree structure of a codebase, based on the specified execution mode and root directory.
- **Inputs**:
    - `codebase_name`: A string representing the name of the codebase for which the file tree DAG is being built.
    - `content`: A dictionary mapping file paths (as strings) to `TechDocsContent` objects, representing the content of each file or directory in the codebase.
    - `codebase_root`: An optional string representing the root directory of the codebase; if `None`, it is determined based on the execution mode.
    - `exeuction_mode`: An `ExecutionMode` enum value indicating whether the code is running locally or in a different mode, affecting how the root directory is determined.
- **Control Flow**:
    - Check if the execution mode is LOCAL and the codebase root is None; if so, set the codebase root to the local path from `LOCAL_FILES` using the codebase name.
    - If the codebase root is not None, convert it to a `Path` object.
    - Create a set of included nodes from the keys of the `content` dictionary, representing the files and directories to be included in the DAG.
    - Initialize an empty dictionary `dag` to store the DAG structure.
    - Use `os.walk` to iterate over the directory structure starting from the `codebase_root` combined with `codebase_name`.
    - For each directory, add its subdirectories and files to the `children` set if they are in the included nodes.
    - For each file, add it to the `dag` with an empty set of children if it is in the included nodes.
    - Add the current directory to the `dag` with its `children` if it is in the included nodes.
    - Return the constructed `dag` dictionary.
- **Output**:
    - A dictionary where keys are file or directory paths (as strings) and values are sets of strings representing the paths of their children, forming a DAG of the file tree.


---
### build_state_filename 
The `build_state_filename` function generates a filename for a state file based on a list of scope roots, a format string, and an optional file extension.
- **Inputs**:
    - `scope_roots`: A list of strings representing the root paths of the scope for which the state filename is being generated.
    - `fmt`: A string representing the format or type of the state file, which will be included in the filename.
    - `ext`: An optional string representing the file extension, defaulting to ".json".
- **Control Flow**:
    - The function begins by extracting target names from the `scope_roots` list using the `_get_target_name` function, which retrieves the name of the path.
    - It uses a dictionary to remove duplicates from the list of target names and then converts it back to a list, taking only the first three unique target names.
    - These target names are joined with underscores to form a base name for the file.
    - The function returns a formatted string that combines the base name, the format string, and the file extension to create the final filename.
- **Output**:
    - A string representing the constructed filename for the state file, formatted as "<name>_<fmt>_iterations<ext>".


---
### build_subgraph 
The `build_subgraph` function constructs a subgraph from a given directed acyclic graph (DAG) starting from a specified node.
- **Inputs**:
    - `dag`: A dictionary representing a directed acyclic graph (DAG) where keys are node identifiers and values are sets of child node identifiers.
    - `start`: A string representing the starting node from which the subgraph should be built.
- **Control Flow**:
    - Check if the start node is present in the DAG; if not, raise a ValueError.
    - Initialize an empty dictionary `subgraph` to store the resulting subgraph.
    - Define a recursive helper function `dfs` to perform a depth-first search starting from the given node.
    - In `dfs`, check if the node is already in `subgraph`; if so, return to avoid revisiting.
    - Add the node to `subgraph` with its children from `dag`.
    - Recursively call `dfs` on each child of the current node.
    - Invoke `dfs` starting from the `start` node.
    - Return the constructed `subgraph`.
- **Output**:
    - A dictionary representing the subgraph of the DAG starting from the specified node, including all reachable nodes and their children.


---
### dfs 
The `dfs` function performs a depth-first search to build a subgraph from a directed acyclic graph (DAG) starting from a given node.
- **Inputs**:
    - `node`: A string representing the starting node for the depth-first search in the DAG.
- **Control Flow**:
    - Check if the node is already in the subgraph; if so, return immediately to avoid revisiting.
    - Add the node to the subgraph with its children copied from the DAG.
    - Iterate over each child of the current node and recursively call `dfs` on each child.
- **Output**:
    - The function does not return any value; it modifies the global `subgraph` dictionary in place to include nodes and their children from the DAG.


---
### get_autodoc_elapsed_time 
The `get_autodoc_elapsed_time` function calculates the time elapsed between the first and last status updates for a specific page and function call in the AutoDocStatusHistory database.
- **Inputs**:
    - `page_id`: A string representing the unique identifier of the page for which the elapsed time is being calculated.
- **Control Flow**:
    - The function imports necessary modules and classes, including `modal`, `async_engine`, `AutoDocStatusHistory`, and `AsyncSession`.
    - It retrieves the current function call ID using `modal.current_function_call_id()`.
    - An asynchronous session is created with `AsyncSession` using the `async_engine`.
    - A SQL query is executed to select all records from `AutoDocStatusHistory` where `page_node_id` matches `page_id` and `call_id` matches the current function call ID, ordered by `created_at` in ascending order.
    - The query results are stored in `states`, and the first and last entries are identified as `start_state` and `end_state`, respectively.
    - The elapsed time is calculated as the difference between `end_state.created_at` and `start_state.created_at`.
    - The function returns the total seconds of the elapsed time as a float.
- **Output**:
    - A float representing the total elapsed time in seconds between the first and last status updates for the specified page and function call.


---
### llm_generate 
The `llm_generate` function asynchronously generates a response from a language model using given system and user prompts, handling request limits and errors.
- **Inputs**:
    - `llm`: An instance of the `ChatOpenAI` class, representing the language model to generate a response from.
    - `system_prompt`: A string representing the system prompt to guide the language model's response.
    - `user_prompt`: A string representing the user prompt to guide the language model's response.
- **Control Flow**:
    - The function enters an asynchronous context with `OPENAI_SEM` and `OPENAI_LIMITER` to manage concurrent requests and rate limits.
    - It attempts to generate a response from the language model using the `generate_response` method with the provided prompts.
    - If a `BadRequestError` is raised by the OpenAI API, it catches the exception, logs an error message with the first 1000 characters of the `user_prompt`, and returns an empty string.
- **Output**:
    - The function returns a string, which is the response generated by the language model, or an empty string if a `BadRequestError` occurs.


---
### main 
The `main` function processes command-line arguments to either validate, execute, or resume a document generation process based on a given configuration file.
- **Inputs**:
    - `args`: An `argparse.Namespace` object containing command-line arguments, which include options for validation, execution, resumption, and a quiet mode.
- **Control Flow**:
    - Check if `args.validate` is provided; if so, load and validate the configuration file, and print the configuration if not in quiet mode.
    - If `args.execute` is provided, initialize the document generation process using the configuration file, generate the document, and print it if not in quiet mode.
    - If `args.resume` is provided, load the previous state from disk, resume the document generation process, and print the document if not in quiet mode.
    - If none of the above options are provided, do nothing.
- **Output**:
    - The function does not return any value; it performs actions based on the command-line arguments.


---
### update_autodocs_status 
The `update_autodocs_status` function asynchronously updates the status of an AutoDoc process in the database by adding a new entry to the AutoDocStatusHistory table.
- **Inputs**:
    - `page_id`: A string representing the unique identifier of the page node for which the status is being updated.
    - `status_kind`: An instance of AutoDocStatusMessageKind, representing the type of status message to be recorded.
    - `content`: A string containing the content or message associated with the status update.
- **Control Flow**:
    - Import necessary modules and classes, including modal, async_engine, AutoDocStatusHistory, and AsyncSession.
    - Retrieve the current function call ID using modal.current_function_call_id().
    - Create an asynchronous session with the database using AsyncSession and begin a transaction.
    - Create an instance of AutoDocStatusHistory with the provided page_id, status_kind, content, and call_id.
    - Add the status_update instance to the session.
    - Commit the transaction to save the changes to the database.
- **Output**:
    - The function does not return any value; it performs a database update operation asynchronously.


