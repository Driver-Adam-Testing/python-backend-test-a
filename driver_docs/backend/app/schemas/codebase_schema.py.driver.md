# Purpose
This Python file defines a set of data models using the Pydantic library, which is commonly used for data validation and settings management in Python applications. The primary purpose of this file is to provide structured representations for various requests and responses related to codebase analysis and generation processes. The models include `CodebaseAnalysisRequest`, `CodebaseGenerationRequest`, `CodebaseGenerationResponse`, `CodebaseAnalysisResponse`, `ModalFunctionCallResponse`, `CodebaseAnalysisMetrics`, `CodebaseAnalysisResult`, and `CodebaseOnboardRequest`. Each class inherits from `BaseModel`, ensuring that the data structures are validated and serialized correctly.

The file is designed to be part of a larger system, likely involving codebase management or analysis services. It includes models for handling requests to analyze or generate codebases, as well as responses that include status updates and results. The `CodebaseAnalysisMetrics` class is particularly detailed, providing computed properties to convert byte counts into source lines of code (SLOC), which is a common metric in software analysis. The use of `Literal` types for status fields ensures that only predefined status values are allowed, enhancing the robustness of the data models. This file is intended to be imported and used in other parts of the application, serving as a foundational component for managing and processing codebase-related data.
# Imports and Dependencies

---
- `uuid`
- `typing.Literal`
- `pydantic.BaseModel`
- `pydantic.computed_field`
- `shared.usage.utils.bytes_to_sloc`


# Global Variables

---
### error 
- **Type**: `Optional[str]`
- **Description**: The `error` variable is an optional string attribute in the `ModalFunctionCallResponse` and `CodebaseAnalysisResult` classes. It is used to store error messages or descriptions when the status of a function call or analysis result is 'error'.
- **Use**: This variable is used to capture and convey error information in the response objects of function calls and codebase analysis results.


---
### frozen 
- **Type**: `bool`
- **Description**: The `frozen` variable is a configuration option within the `Config` class of the `CodebaseAnalysisMetrics` model, set to `True`. This indicates that the model is immutable, meaning that once an instance of `CodebaseAnalysisMetrics` is created, its fields cannot be modified.
- **Use**: This variable is used to enforce immutability on instances of the `CodebaseAnalysisMetrics` class, ensuring data integrity by preventing changes to the instance's state after creation.


---
### response 
- **Type**: `dict | None`
- **Description**: The `response` variable is a dictionary or None, defined as part of the `ModalFunctionCallResponse` class. It is used to store the response data from a modal function call, which can vary depending on the context of the call.
- **Use**: This variable is used to hold the response data from a modal function call, allowing the program to access and process the results of the call.


---
### result 
- **Type**: `CodebaseAnalysisMetrics | None`
- **Description**: The `result` variable is an instance of the `CodebaseAnalysisMetrics` class or `None`. It is part of the `CodebaseAnalysisResult` class, which represents the outcome of a codebase analysis operation. The `CodebaseAnalysisMetrics` class contains detailed metrics about the codebase, such as the number of analyzable bytes, files, and lines of code (SLOC), categorized by file extension and type.
- **Use**: This variable is used to store the metrics resulting from a codebase analysis, providing detailed insights into the codebase's structure and content.


---
### status 
- **Type**: `Literal['pending', 'running', 'completed', 'error', 'expired']`
- **Description**: The `status` variable is a string literal that represents the current state of a process or operation. It can take one of five predefined values: 'pending', 'running', 'completed', 'error', or 'expired'. These values indicate the progress or outcome of a task.
- **Use**: This variable is used to track and communicate the current state of a process within the `ModalFunctionCallResponse` and `CodebaseAnalysisResult` classes.


# Classes

---
### CodebaseAnalysisMetrics 
- **Type**: `class`
- **Members**:
    - `analyzable_bytes`: The number of bytes in the codebase that can be analyzed.
    - `total_bytes`: The total number of bytes in the codebase.
    - `analyzable_files`: The number of files in the codebase that can be analyzed.
    - `total_files`: The total number of files in the codebase.
    - `analyzable_files_by_extension`: A dictionary mapping file extensions to the number of analyzable files with that extension.
    - `analyzable_files_by_type`: A dictionary mapping file types to the number of analyzable files of that type.
    - `analyzable_bytes_by_extension`: A dictionary mapping file extensions to the number of analyzable bytes for files with that extension.
    - `analyzable_bytes_by_type`: A dictionary mapping file types to the number of analyzable bytes for files of that type.
    - `analyzable_sloc`: The number of source lines of code (SLOC) that can be analyzed, computed from analyzable bytes.
    - `total_sloc`: The total number of source lines of code (SLOC) in the codebase, computed from total bytes.
    - `analyzable_sloc_by_extension`: A dictionary mapping file extensions to the number of analyzable SLOC for files with that extension.
    - `analyzable_sloc_by_type`: A dictionary mapping file types to the number of analyzable SLOC for files of that type.
- **Description**: The `CodebaseAnalysisMetrics` class is a data model that encapsulates various metrics related to the analysis of a codebase, such as the number of analyzable bytes and files, both in total and broken down by file extension and type. It provides computed properties to convert byte counts into source lines of code (SLOC) for both total and analyzable metrics, facilitating a detailed understanding of the codebase's composition and size. The class is immutable, as indicated by the frozen configuration.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### CodebaseAnalysisMetrics.analyzable_sloc
The `analyzable_sloc` function calculates the source lines of code (SLOC) from the analyzable bytes of a codebase.
- **Inputs**:
    - `self`: An instance of the CodebaseAnalysisMetrics class, which contains various metrics about the codebase, including analyzable bytes.
- **Control Flow**:
    - The function accesses the `analyzable_bytes` attribute from the `self` instance, which represents the number of bytes in the codebase that are analyzable.
    - It calls the `bytes_to_sloc` utility function, passing the `analyzable_bytes` as an argument to convert the byte count into source lines of code (SLOC).
    - The result from `bytes_to_sloc` is returned as the output of the function.
- **Output**:
    - The function returns an integer representing the source lines of code (SLOC) calculated from the analyzable bytes of the codebase.


---
#### CodebaseAnalysisMetrics.analyzable_sloc_by_extension
The function `analyzable_sloc_by_extension` calculates the source lines of code (SLOC) for each file extension based on the analyzable bytes.
- **Inputs**:
    - None
- **Control Flow**:
    - The function accesses the `analyzable_bytes_by_extension` dictionary from the class instance, which maps file extensions to their corresponding byte counts.
    - It iterates over each key-value pair in the `analyzable_bytes_by_extension` dictionary.
    - For each pair, it converts the byte count to SLOC using the `bytes_to_sloc` function and stores the result in a new dictionary with the same keys (file extensions).
    - The function returns the newly created dictionary mapping file extensions to their SLOC values.
- **Output**:
    - A dictionary mapping file extensions (as strings) to their corresponding source lines of code (SLOC) counts (as integers).


---
#### CodebaseAnalysisMetrics.analyzable_sloc_by_type
The function `analyzable_sloc_by_type` converts the number of analyzable bytes by type into source lines of code (SLOC) for each type.
- **Inputs**:
    - None
- **Control Flow**:
    - The function accesses the `analyzable_bytes_by_type` dictionary from the instance of the class it belongs to.
    - It iterates over each key-value pair in the `analyzable_bytes_by_type` dictionary.
    - For each pair, it converts the byte count (value) to SLOC using the `bytes_to_sloc` function.
    - It constructs a new dictionary with the same keys but with values converted to SLOC.
    - The function returns the newly constructed dictionary.
- **Output**:
    - A dictionary where each key is a type and each value is the corresponding source lines of code (SLOC) calculated from the analyzable bytes.


---
#### CodebaseAnalysisMetrics.total_sloc
The `total_sloc` function calculates the total source lines of code (SLOC) from the total bytes of code.
- **Inputs**:
    - `self`: An instance of the `CodebaseAnalysisMetrics` class, which contains the `total_bytes` attribute representing the total bytes of code.
- **Control Flow**:
    - The function accesses the `total_bytes` attribute from the `self` object, which is an instance of `CodebaseAnalysisMetrics`.
    - It calls the `bytes_to_sloc` function, passing `self.total_bytes` as an argument to convert the total bytes into source lines of code (SLOC).
    - The result from `bytes_to_sloc` is returned as the output of the function.
- **Output**:
    - The function returns an integer representing the total source lines of code (SLOC) calculated from the total bytes of code.


**Nested Classes**
    - Config


---
### CodebaseAnalysisRequest 
- **Type**: `class`
- **Members**:
    - `download_url`: A string representing the URL from which the codebase can be downloaded.
- **Description**: The `CodebaseAnalysisRequest` class is a simple data model that inherits from `BaseModel` and is used to encapsulate the request data for analyzing a codebase. It contains a single attribute, `download_url`, which specifies the URL from which the codebase can be downloaded for analysis.
- **Inherits From**:
    - BaseModel


---
### CodebaseAnalysisResponse 
- **Type**: `class`
- **Members**:
    - `call_id`: A string identifier for the call associated with the codebase analysis.
    - `codebase_object_key`: A string key representing the codebase object being analyzed.
- **Description**: The `CodebaseAnalysisResponse` class is a simple data model that inherits from `BaseModel` and is used to encapsulate the response data for a codebase analysis operation. It contains two string fields: `call_id`, which uniquely identifies the analysis call, and `codebase_object_key`, which represents the key of the codebase object that was analyzed. This class is part of a larger system for managing codebase analysis requests and responses.
- **Inherits From**:
    - BaseModel


---
### CodebaseAnalysisResult 
- **Type**: `class`
- **Members**:
    - `call_id`: A unique identifier for the analysis call.
    - `status`: The current status of the analysis, which can be 'pending', 'running', 'completed', 'error', or 'expired'.
    - `result`: An optional field containing the metrics of the codebase analysis if available.
    - `error`: An optional field containing error information if the analysis encountered an issue.
- **Description**: The CodebaseAnalysisResult class is a data model that represents the outcome of a codebase analysis operation. It includes a unique call identifier, the status of the analysis, and optionally, the results of the analysis or any error encountered. This class is useful for tracking the progress and results of codebase analysis tasks.
- **Inherits From**:
    - BaseModel


---
### CodebaseGenerationRequest 
- **Type**: `class`
- **Members**:
    - `version_ids`: A list of UUIDs representing version identifiers for the codebase generation request.
- **Description**: The `CodebaseGenerationRequest` class is a data model that represents a request to generate a codebase, specifically containing a list of version identifiers in the form of UUIDs. It inherits from Pydantic's `BaseModel`, which provides data validation and serialization capabilities.
- **Inherits From**:
    - BaseModel


---
### CodebaseGenerationResponse 
- **Type**: `class`
- **Members**:
    - `call_id`: A string identifier for the call associated with the codebase generation response.
- **Description**: The `CodebaseGenerationResponse` class is a simple data model that inherits from `BaseModel` and is used to represent the response of a codebase generation request. It contains a single attribute, `call_id`, which serves as a unique identifier for the call related to the codebase generation process.
- **Inherits From**:
    - BaseModel


---
### CodebaseOnboardRequest 
- **Type**: `class`
- **Members**:
    - `codebase_object_key`: A string representing the key of the codebase object.
    - `call_id`: A string representing the call identifier.
- **Description**: The `CodebaseOnboardRequest` class is a simple data model that inherits from `BaseModel` and is used to encapsulate the request data for onboarding a codebase. It contains two string fields: `codebase_object_key`, which identifies the codebase object, and `call_id`, which serves as a unique identifier for the request call.
- **Inherits From**:
    - BaseModel


---
### Config 
- **Type**: `class`
- **Members**:
    - `frozen`: Indicates that the configuration is immutable.
- **Description**: The `Config` class is a simple configuration class used within the `CodebaseAnalysisMetrics` class to specify that instances of this class are immutable. This is achieved by setting the `frozen` attribute to `True`, which is a common pattern in Pydantic models to ensure that once an instance is created, its fields cannot be modified.


---
### ModalFunctionCallResponse 
- **Type**: `class`
- **Members**:
    - `call_id`: A unique identifier for the function call.
    - `status`: The current status of the function call, which can be 'pending', 'running', 'completed', 'error', or 'expired'.
    - `response`: An optional dictionary containing the response data from the function call.
    - `error`: An optional string describing any error that occurred during the function call.
- **Description**: The `ModalFunctionCallResponse` class is a data model that represents the response of a modal function call, including its unique identifier, current status, optional response data, and any error message. It is used to track and manage the state and outcome of asynchronous function calls within a system.
- **Inherits From**:
    - BaseModel


