# Purpose
This Python code file is designed to facilitate the generation and rendering of structured markdown documentation from raw symbol data, likely extracted from source code. The file defines a series of classes and functions that collectively form a framework for converting code symbols into markdown format, which can be used for documentation purposes. The core functionality revolves around the `MdRenderable` abstract base class, which provides a blueprint for rendering markdown content. Several concrete classes inherit from `MdRenderable`, each tailored to render different types of content, such as raw text, field names with content, and lists of content, into markdown format.

The file also includes classes like `IrData` and `IrCollection`, which are abstract base classes intended to be extended for specific types of code symbols, such as variables, data structures, functions, and classes. These classes provide methods for generating instances from language model responses, rendering markdown, and managing child symbols. The code leverages concurrent processing to handle multiple symbols efficiently, using a thread pool executor to parallelize the generation of documentation for each symbol. This setup suggests that the code is part of a larger system that uses language models, such as OpenAI's GPT, to analyze and document codebases, making it a specialized tool for automated code documentation.
# Imports and Dependencies

---
- `__future__.annotations`
- `abc`
- `concurrent.futures`
- `re`
- `collections.defaultdict`
- `math.ceil`
- `typing.Self`
- `openai`
- `pydantic.BaseModel`
- `pydantic.PrivateAttr`
- `utils.lang_specialization.symbol_common.RawSymbolCollection`
- `utils.lang_specialization.symbol_common.RawSymbolData`
- `utils.lang_specialization.symbol_common.ReifiedSymbol`
- `utils.lang_specialization.symbol_common.ScopeRelation`
- `utils.lang_specialization.symbol_common.SymbolKind`
- `utils.models.ChatOpenAI`
- `utils.models.OutputConfig`
- `utils.models.OutputConfigKind`
- `utils.threadpool.FastShutdownThreadPoolExecutor`


# Global Variables

---
### MAX_SYMBOLS_PER_WORKER 
- **Type**: `int`
- **Description**: `MAX_SYMBOLS_PER_WORKER` is a global integer variable set to 50. It defines the maximum number of symbols that can be processed by a single worker in a concurrent execution environment.
- **Use**: This variable is used to determine the number of workers needed for processing symbols by dividing the total number of symbols by `MAX_SYMBOLS_PER_WORKER`.


---
### MAX_WORKERS_FOR_SYMBOLS 
- **Type**: `int`
- **Description**: `MAX_WORKERS_FOR_SYMBOLS` is a global constant integer variable set to 10. It represents the maximum number of worker threads that can be used for processing symbols concurrently.
- **Use**: This variable is used to limit the number of concurrent workers in the `compute_num_workers` function.


---
### _children 
- **Type**: `list`
- **Description**: The `_children` variable is a private attribute of the `IrData` class, initialized as an empty list by default. It is intended to store child elements associated with an instance of `IrData`. These child elements are typically tuples containing a `RawSymbolData` object and its corresponding `IrData` instance or `None`. This structure allows for the organization and management of hierarchical data within the `IrData` class.
- **Use**: This variable is used to store and manage child elements related to an `IrData` instance, facilitating the rendering and processing of hierarchical data structures.


---
### _reified_symbol 
- **Type**: `ReifiedSymbol | None`
- **Description**: The `_reified_symbol` is a private attribute of the `IrData` class, which is either an instance of `ReifiedSymbol` or `None`. It is used to store additional information about a symbol, such as its kind and any calls it makes, which can be rendered later.
- **Use**: This variable is used to store and later render information about a symbol's kind and its calls, if available.


---
### _supported_child_ordering 
- **Type**: `list[str]`
- **Description**: The `_supported_child_ordering` is a private attribute of the `ClassData` class, which is a list of strings representing the order in which child elements should be rendered. It is initialized with a default value containing `ScopeRelation.METHOD` and `ScopeRelation.NESTED_CLASS`, indicating that methods and nested classes are the supported child types for ordering.
- **Use**: This variable is used to define the order in which child elements of a class are rendered in the markdown output.


# Classes

---
### ClassData 
- **Type**: `class`
- **Members**:
    - `type`: Specifies the type of the class with backtick content.
    - `members`: Holds a list of named content items representing class members.
    - `description`: Provides a raw content description of the class.
    - `inherits_from`: Lists the classes from which this class inherits.
    - `_supported_child_ordering`: Defines the order of supported child elements, such as methods and nested classes.
- **Description**: The `ClassData` class is an abstract base class that extends `IrData` and is designed to represent metadata about a class, including its type, members, description, and inheritance information. It includes a class method `default_instance` to create a default instance with predefined content. The class also maintains a private attribute `_supported_child_ordering` to specify the order of child elements like methods and nested classes. This class is part of a larger framework for rendering markdown documentation from structured data.
- **Inherits From**:
    - IrData
    - abc.ABC

**Methods**

---
#### ClassData.default_instance
The `default_instance` function creates a default instance of a class with predefined attributes.
- **Inputs**:
    - `cls`: The class for which a default instance is to be created.
- **Control Flow**:
    - The function is called with a class as an argument.
    - It returns an instance of the class with specific attributes set to default values.
- **Output**:
    - An instance of the class `cls` with default attributes: `description`, `type`, `members`, and `inherits_from`.



---
### DataStructureData 
- **Type**: `class`
- **Members**:
    - `type`: Represents the type of the data structure with backtick content.
    - `members`: Holds a list of named content items representing the members of the data structure.
    - `description`: Provides a raw content description of the data structure.
- **Description**: The `DataStructureData` class is an abstract base class that extends `IrData` and is designed to represent data structures with specific attributes such as type, members, and description. It provides a method `default_instance` to create a default instance of the class with empty or default values for its attributes. This class is part of a larger framework for rendering markdown documentation from structured data, and it relies on other classes to define the format and content of its attributes.
- **Inherits From**:
    - IrData
    - abc.ABC

**Methods**

---
#### DataStructureData.default_instance
The `default_instance` function creates and returns a default instance of the class with predefined empty or default values for its attributes.
- **Inputs**:
    - `cls`: The class for which a default instance is to be created.
- **Control Flow**:
    - The function is a class method that takes the class itself as an argument.
    - It returns an instance of the class by calling the class constructor with specific default values for its attributes.
    - The attributes 'type', 'members', and 'description' are initialized with empty or default values.
- **Output**:
    - An instance of the class with default values for its attributes.



---
### FieldNameWithBackTickContent 
- **Type**: `class`
- **Members**:
    - `content`: A string representing the content to be rendered in markdown format.
- **Description**: The `FieldNameWithBackTickContent` class is a subclass of `MdRenderable` that represents a field with content that is rendered in markdown format with the content enclosed in backticks. It provides a method `render_markdown` that formats the content with a label, converting the label from snake_case to a spaced string, and returns it as a markdown string.
- **Inherits From**:
    - MdRenderable

**Methods**

---
#### FieldNameWithBackTickContent.render_markdown
The `render_markdown` function formats a given document label and content into a markdown string with a specific structure.
- **Inputs**:
    - `doc_label`: A string representing the document label, which is expected to be in snake_case format.
- **Control Flow**:
    - The function calls `snake_case_to_spaced_string` to convert the `doc_label` from snake_case to a spaced string format.
    - It then formats the converted label and the `content` attribute of the class instance into a markdown string with a specific structure, including backticks around the content.
- **Output**:
    - A string formatted in markdown, with the document label in bold and the content enclosed in backticks, followed by a newline.



---
### FieldNameWithBulletedContent 
- **Type**: `class`
- **Members**:
    - `content`: A string representing the content to be rendered in markdown format.
- **Description**: The `FieldNameWithBulletedContent` class is a subclass of `MdRenderable` designed to render markdown content with a specific format. It takes a string `content` and a `doc_label`, converting the `doc_label` from snake_case to a spaced string, and formats the content as a bulleted list under the label. This class is useful for generating markdown documentation where content needs to be presented in a structured, bulleted format.
- **Inherits From**:
    - MdRenderable

**Methods**

---
#### FieldNameWithBulletedContent.render_markdown
The `render_markdown` function formats a given document label and content into a markdown string with a bullet point and sub-bullet point.
- **Inputs**:
    - `doc_label`: A string representing the document label to be formatted in markdown.
- **Control Flow**:
    - The function calls `snake_case_to_spaced_string` to convert the `doc_label` from snake_case to a spaced string.
    - It then formats the converted label and the instance's `content` attribute into a markdown string with a bullet point and sub-bullet point.
- **Output**:
    - A markdown formatted string with the document label as a bullet point and the content as a sub-bullet point.



---
### FieldNameWithRawContent 
- **Type**: `class`
- **Members**:
    - `content`: A string representing the raw content to be rendered.
- **Description**: The `FieldNameWithRawContent` class is a subclass of `MdRenderable` designed to render markdown content with a specific format. It contains a single string attribute `content` and implements the `render_markdown` method to format the content with a label, converting the label from snake_case to a spaced string format. This class is useful for generating markdown documentation with a consistent style.
- **Inherits From**:
    - MdRenderable

**Methods**

---
#### FieldNameWithRawContent.render_markdown
The `render_markdown` function formats a given document label and content into a markdown string with a specific structure.
- **Inputs**:
    - `doc_label`: A string representing the document label in snake_case format.
- **Control Flow**:
    - The function calls `snake_case_to_spaced_string` to convert the `doc_label` from snake_case to a spaced string.
    - It then formats the converted label and the instance's `content` attribute into a markdown string with a specific bullet point structure.
- **Output**:
    - A string formatted in markdown with the document label converted to spaced string and the content included.



---
### FnData 
- **Type**: `class`
- **Members**:
    - `single_sentence`: A brief description of the function.
    - `inputs`: A list of inputs with their names and descriptions.
    - `control_flow`: A list of control flow elements within the function.
    - `output`: The output of the function, described in a bulleted format.
- **Description**: The `FnData` class is an abstract base class that extends `IrData` and is designed to represent function data in a structured format. It includes attributes for a single sentence description, inputs, control flow elements, and output, each of which is rendered in a markdown format. The class provides a method to create a default instance with empty or default values for each attribute.
- **Inherits From**:
    - IrData
    - abc.ABC

**Methods**

---
#### FnData.default_instance
The `default_instance` function creates and returns a default instance of the class it is called on, with specific default values for its attributes.
- **Inputs**:
    - `cls`: The class on which the method is called, representing the class itself.
- **Control Flow**:
    - The function is a class method that takes the class itself as an argument.
    - It returns an instance of the class with predefined default values for its attributes.
- **Output**:
    - An instance of the class with default values for the attributes `single_sentence`, `inputs`, `control_flow`, and `output`.



---
### FnDeclData 
- **Type**: `class`
- **Members**:
    - `single_sentence`: A brief description of the function in raw content format.
    - `description`: A detailed description of the function in raw content format.
    - `inputs`: A list of named content representing the inputs to the function, which can be empty.
    - `output`: A detailed description of the function's output in raw content format.
- **Description**: The `FnDeclData` class is an abstract base class that extends `IrData` and is designed to represent the declaration of a function. It includes attributes for a single sentence summary, a detailed description, inputs, and output of the function. The class provides a class method `default_instance` to create a default instance with empty content for all fields. This class is part of a larger framework for rendering markdown documentation from structured data.
- **Inherits From**:
    - IrData
    - abc.ABC

**Methods**

---
#### FnDeclData.default_instance
The `default_instance` function creates and returns a default instance of the class it is called on, with specific fields initialized to empty or default values.
- **Inputs**:
    - `cls`: The class on which the `default_instance` method is called, typically a subclass of `IrData` or similar.
- **Control Flow**:
    - The function is called as a class method, indicated by the `cls` parameter.
    - It returns an instance of the class `cls` with specific fields initialized to default values.
    - The fields `single_sentence`, `description`, `inputs`, and `output` are initialized with instances of `RawContent`, `FieldNameWithRawContent`, `ListedBacktickNameRawContentWithNone`, and `FieldNameWithRawContent` respectively, all with empty or default content.
- **Output**:
    - An instance of the class `cls` with specific fields initialized to default values.



---
### IrCollection 
- **Type**: `class`
- **Members**:
    - `data`: A dictionary mapping strings to either IrData instances or lists of IrData instances.
- **Description**: The `IrCollection` class is an abstract base class that extends `BaseModel` and is designed to manage a collection of intermediate representation (IR) data. It provides methods to construct an instance from a language model (LLM) and a collection of raw symbols, leveraging concurrent processing to handle multiple symbols efficiently. The class also includes functionality to render the IR data into markdown format, making it suitable for documentation purposes. The `IrCollection` class is abstract and requires subclasses to implement the `from_llm` method.
- **Inherits From**:
    - BaseModel
    - abc.ABC

**Methods**

---
#### IrCollection.__str__
The `__str__` function returns the markdown representation of the object.
- **Inputs**:
    - `self`: The instance of the class that implements the `__str__` method.
- **Control Flow**:
    - The function calls the `render_markdown` method on the `self` object.
    - The result of `render_markdown` is returned as the output of the function.
- **Output**:
    - A string containing the markdown representation of the object.


---
#### IrCollection.from_llm
The `from_llm` function is a class method that creates an instance of the class using a language model and a collection of raw symbols.
- **Inputs**:
    - `cls`: The class itself, which is being instantiated.
    - `llm`: An instance of the `ChatOpenAI` class, representing the language model to be used for generating responses.
    - `symbols_list`: An instance of `RawSymbolCollection`, which contains a collection of raw symbols to be processed.
- **Control Flow**:
    - The function is defined as a class method, indicated by the `cls` parameter.
    - The function takes a language model (`llm`) and a collection of symbols (`symbols_list`) as inputs.
    - The function is currently not implemented, as indicated by the `pass` statement.
- **Output**:
    - The function is intended to return an instance of the class (`Self`), but currently, it does not return anything due to the lack of implementation.


---
#### IrCollection.from_llm_with_ir_data
The `from_llm_with_ir_data` function processes a collection of raw symbols using a language model to generate intermediate representation data.
- **Inputs**:
    - `ir_data`: A type of `IrData` that defines how to process each symbol into an intermediate representation.
    - `llm`: An instance of `ChatOpenAI` used to generate responses for each symbol.
    - `symbols_list`: A `RawSymbolCollection` containing the raw symbols to be processed.
- **Control Flow**:
    - Initialize an empty dictionary `symbols_dict` and an empty dictionary `futures` to store future tasks.
    - Compute the number of workers needed based on the number of symbols in `symbols_list`.
    - Select the language model to use based on the number of workers.
    - Create a thread pool executor with the computed number of workers.
    - Iterate over each symbol in `symbols_list.data`.
    - For each symbol, submit a task to the executor to process the symbol using `ir_data.from_llm` and store the future in `futures`.
    - Raise a `ValueError` if an unsupported type is found in `symbols_list`.
    - As each future completes, retrieve the result and append it to the corresponding entry in `symbols_dict`.
    - Return an instance of the class with `symbols_dict` as its data.
- **Output**:
    - An instance of the class with a dictionary of processed symbols as its data.


---
#### IrCollection.render_markdown
The `render_markdown` function generates a markdown representation of the data stored in the `IrCollection` class, including optional symbol metadata.
- **Inputs**:
    - `self`: An instance of the `IrCollection` class containing a dictionary of data to be rendered as markdown.
- **Control Flow**:
    - Initialize an empty string `output` to accumulate the markdown content.
    - Iterate over each key-value pair in `self.data.items()`.
    - For each item in the list `v`, check if the item has a `_reified_symbol`.
    - If `_reified_symbol` is present, construct an `id_comment` using the symbol's kind and name.
    - Append a markdown header with the key `k` and the `id_comment` to `output`.
    - Call `render_markdown` on the item and append the result to `output`.
    - Return the accumulated `output` string.
- **Output**:
    - A string containing the markdown representation of the data, including headers and optional symbol metadata comments.



---
### IrData 
- **Type**: `class`
- **Members**:
    - `_children`: A private attribute that stores a list of child elements.
    - `_supported_child_ordering`: A private attribute that defines the order in which child elements should be rendered.
    - `_reified_symbol`: A private attribute that holds a reified symbol, if available.
- **Description**: The `IrData` class is an abstract base class that extends `BaseModel` and provides a framework for handling intermediate representation (IR) data. It includes private attributes for managing child elements and their rendering order, as well as a reified symbol for additional metadata. The class defines several abstract methods that subclasses must implement, such as `system_prompt`, `user_prompt`, `child_to_ir`, `child_to_field_name`, and `default_instance`. It also includes a concrete method `from_llm` for creating instances from a language model and a `render_markdown` method for generating markdown representations of the data.
- **Inherits From**:
    - BaseModel
    - abc.ABC

**Methods**

---
#### IrData.child_to_field_name
The `child_to_field_name` function is an abstract method intended to map a `RawSymbolData` child to a corresponding field name as a string.
- **Inputs**:
    - `cls`: The class object that this method is a part of, typically used to access class-level attributes or methods.
    - `child`: An instance of `RawSymbolData` representing a child symbol whose field name needs to be determined.
- **Control Flow**:
    - The function is defined as an abstract method using the `abc.abstractmethod` decorator, indicating that any subclass must implement this method.
    - The function takes two parameters: `cls` and `child`, but the body of the function is not implemented (indicated by `pass`), meaning it serves as a placeholder for subclasses to provide specific logic.
- **Output**:
    - The function is expected to return a string representing the field name corresponding to the given `RawSymbolData` child.


---
#### IrData.child_to_ir
The `child_to_ir` function determines the appropriate `IrData` type for a given `RawSymbolData` or returns `None` if no additional IR content is needed.
- **Inputs**:
    - `symbol`: A `RawSymbolData` object representing a symbol for which the IR type needs to be determined.
- **Control Flow**:
    - The function is a placeholder and does not contain any implemented logic.
    - The function is intended to return `None` for symbols that do not require additional IR content, such as nested classes that are just listed.
- **Output**:
    - The function returns a type of `IrData` or `None` if no additional IR content is needed.


---
#### IrData.default_instance
The `default_instance` function is an abstract class method intended to return a default instance of the class it belongs to.
- **Inputs**:
    - `cls`: The class itself, which is a standard convention for class methods to refer to the class object.
- **Control Flow**:
    - The function is defined as an abstract class method, indicating that it must be implemented by any subclass.
    - The function currently has no implementation (indicated by `pass`), meaning it serves as a placeholder for subclasses to provide their own implementation.
- **Output**:
    - The function is expected to return an instance of the class (`Self`), but the actual return value is not defined in this abstract method.


---
#### IrData.from_llm
The `from_llm` function generates an instance of a class from a language model response based on a given symbol's data.
- **Inputs**:
    - `cls`: The class type from which an instance will be created.
    - `llm`: An instance of the ChatOpenAI class used to generate responses from a language model.
    - `symbol`: An instance of RawSymbolData containing information about the symbol to be processed.
- **Control Flow**:
    - Check if the symbol's code is None; if so, create a default instance of the class.
    - If the symbol's code is not None, generate a system prompt and user prompt, and use the language model to generate a response.
    - Handle exceptions related to response length and return None if caught.
    - Parse the raw content from the language model response to create an instance of the class.
    - If the symbol has a reified symbol, store it in the class instance for later rendering.
    - If the symbol has children, determine the number of workers needed and process each child symbol concurrently using a thread pool executor.
    - For each child symbol, determine its corresponding IR class and recursively call from_llm to process it, storing the results in the class instance's children list.
    - Return the fully constructed class instance.
- **Output**:
    - An instance of the class `cls` populated with data derived from the language model's response and the provided symbol data.


---
#### IrData.render_markdown
The `render_markdown` function generates a markdown representation of the current object, including its fields, called functions, and child elements.
- **Inputs**:
    - None
- **Control Flow**:
    - Initialize an empty string `output` to accumulate the markdown content.
    - Iterate over each label and content pair in the current object.
    - Check if the content is an instance of `MdRenderable`; if not, raise a `ValueError`.
    - Render the markdown for each label content using its `render_markdown` method.
    - If the object has a `_reified_symbol` of kind `CALLABLE` with calls, replace function names in the rendered content with markdown links to their definitions.
    - Append the rendered content to `output`.
    - If `_reified_symbol` is not `None`, append additional markdown for functions called and related symbols.
    - Create a dictionary `child_dictionary` to store markdown for child elements based on `_supported_child_ordering`.
    - Iterate over each child symbol and content, updating `child_dictionary` with rendered markdown for each child.
    - Append the content of `child_dictionary` to `output`.
    - Return the accumulated `output` string.
- **Output**:
    - A string containing the markdown representation of the object, including its fields, called functions, and child elements.


---
#### IrData.system_prompt
The `system_prompt` function is a placeholder for a class method that is intended to return a string.
- **Inputs**:
    - None
- **Control Flow**:
    - None
- **Output**:
    - The function is expected to return a string, but currently, it does not return anything as it is not implemented.


---
#### IrData.user_prompt
The `user_prompt` function is a placeholder method intended to generate a user prompt string based on a given `RawSymbolData` object.
- **Inputs**:
    - `cls`: The class object that this class method is associated with.
    - `symbol`: An instance of `RawSymbolData` which contains information about a symbol, such as its name, type, and other metadata.
- **Control Flow**:
    - The function is defined as a class method, indicated by the `cls` parameter.
    - The function currently has no implementation, as indicated by the `pass` statement.
- **Output**:
    - The function is expected to return a string, but currently, it does not return anything due to the lack of implementation.



---
### ListData 
- **Type**: `class`
- **Members**:
    - `data`: A list of strings representing the data contained in the instance.
- **Description**: The `ListData` class is a specialized data structure that extends `BaseModel` to handle a list of strings. It provides functionality to create an instance from a language model (LLM) response using the `from_llm` class method, which constructs a complete user prompt and parses the LLM's JSON response into an instance of `ListData`. Additionally, it includes methods to render the data as a markdown string, making it suitable for documentation or display purposes. The `__str__` method is overridden to return the markdown representation of the data, facilitating easy conversion to a human-readable format.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### ListData.__str__
The `__str__` function returns the markdown representation of the object by calling its `render_markdown` method.
- **Inputs**:
    - `self`: The instance of the class that implements the `__str__` method.
- **Control Flow**:
    - The function directly calls the `render_markdown` method on the `self` object.
    - The result of the `render_markdown` method is returned as the output of the `__str__` function.
- **Output**:
    - A string that represents the markdown rendering of the object.


---
#### ListData.from_llm
The `from_llm` function generates an instance of a class by using a language model to process a system and user prompt along with code.
- **Inputs**:
    - `cls`: The class type that the function will return an instance of.
    - `llm`: An instance of the ChatOpenAI class, representing the language model used to generate the response.
    - `system_prompt`: A string containing the system prompt to guide the language model's response.
    - `user_prompt`: A string containing the user prompt to guide the language model's response.
    - `code`: A string containing the code that will be included in the user prompt for the language model to process.
- **Control Flow**:
    - Concatenate the user prompt with the code to form a complete user prompt.
    - Call the `generate_response` method on the `llm` object with the system prompt, complete user prompt, and an output configuration specifying JSON_STRICT and the class type.
    - Parse the raw content returned by the language model into an instance of the class using `cls.parse_raw`.
- **Output**:
    - An instance of the class `cls` populated with data generated by the language model.


---
#### ListData.render_markdown
The `render_markdown` function generates a markdown-formatted string representation of a list of dependencies.
- **Inputs**:
    - `self`: An instance of the ListData class, which contains a list of strings in the 'data' attribute.
- **Control Flow**:
    - Initialize an empty string 'output'.
    - Append a markdown horizontal rule ('---') followed by a newline to 'output'.
    - Iterate over each dependency in 'self.data'.
    - For each dependency, append a markdown list item with the dependency name enclosed in backticks to 'output'.
    - Append a newline to 'output'.
    - Return the 'output' string.
- **Output**:
    - A string formatted in markdown, representing the list of dependencies with each dependency as a list item.



---
### ListedBacktickNameRawContentNoNone 
- **Type**: `class`
- **Members**:
    - `content`: A list of NamedContent objects.
- **Description**: The ListedBacktickNameRawContentNoNone class is designed to render a list of NamedContent objects into a markdown format. It inherits from the MdRenderable class and implements the render_markdown method, which iterates over the content list and generates a markdown string representation for each NamedContent item, prefixed by a label derived from the provided doc_label.
- **Inherits From**:
    - MdRenderable

**Methods**

---
#### ListedBacktickNameRawContentNoNone.render_markdown
The `render_markdown` function generates a markdown-formatted string representation of the content associated with a given document label.
- **Inputs**:
    - `doc_label`: A string representing the label of the document to be rendered in markdown format.
- **Control Flow**:
    - Initialize an empty string `output_str` to accumulate the markdown output.
    - Check if the `content` attribute of the instance is non-empty.
    - If non-empty, append a markdown-formatted header with the document label converted from snake_case to spaced string format.
    - Iterate over each item in the `content` list and append its markdown representation to `output_str` by calling its `render_markdown` method with `doc_label`.
    - Return the accumulated `output_str` as the final markdown output.
- **Output**:
    - A string containing the markdown-formatted representation of the content, prefixed by the document label.



---
### ListedBacktickNameRawContentWithNone 
- **Type**: `class`
- **Members**:
    - `content`: A list of NamedContent objects.
- **Description**: The `ListedBacktickNameRawContentWithNone` class is a subclass of `MdRenderable` designed to render a list of `NamedContent` objects into a markdown format. It includes a method `render_markdown` that generates a markdown string representation of the content, with a specific format for when the list is empty, appending "- None" to indicate the absence of content.
- **Inherits From**:
    - MdRenderable

**Methods**

---
#### ListedBacktickNameRawContentWithNone.render_markdown
The `render_markdown` function generates a markdown-formatted string representation of the content associated with a given document label.
- **Inputs**:
    - `doc_label`: A string representing the document label to be used in the markdown output.
- **Control Flow**:
    - Initialize an empty string `output_str` to accumulate the markdown output.
    - Append a formatted string with the document label converted from snake_case to spaced string format to `output_str`.
    - Check if the `content` attribute of the class instance is non-empty.
    - If `content` is non-empty, iterate over each item in `content` and append the result of calling `render_markdown` on each item with `doc_label` to `output_str`.
    - If `content` is empty, append a markdown-formatted string indicating 'None' to `output_str`.
    - Return the accumulated `output_str` as the final markdown output.
- **Output**:
    - A string containing the markdown-formatted representation of the content, with the document label as a heading and each item's markdown representation listed under it, or 'None' if there are no items.



---
### ListedRawContentNoNone 
- **Type**: `class`
- **Members**:
    - `content`: A list of strings to be rendered as markdown.
- **Description**: The `ListedRawContentNoNone` class is a subclass of `MdRenderable` that is designed to render a list of strings into a markdown format. It provides a method `render_markdown` which takes a document label, converts it into a spaced string, and formats each item in the `content` list as a bullet point under this label. This class ensures that the markdown output does not include a 'None' entry when the list is empty.
- **Inherits From**:
    - MdRenderable

**Methods**

---
#### ListedRawContentNoNone.render_markdown
The `render_markdown` function generates a markdown-formatted string representation of a list of content items, prefixed by a formatted document label.
- **Inputs**:
    - `doc_label`: A string representing the label for the document section, which will be converted from snake_case to a spaced string format.
- **Control Flow**:
    - Initialize an empty string `output_str` to accumulate the markdown output.
    - Check if the `content` attribute of the class instance is non-empty.
    - If non-empty, append a formatted string with the document label converted to spaced string format to `output_str`.
    - Iterate over each item in the `content` list and append it as a bullet point to `output_str`.
    - Return the accumulated `output_str` as the final markdown output.
- **Output**:
    - A markdown-formatted string that includes the document label and a bulleted list of content items, or an empty string if the content list is empty.



---
### ListedRawContentWithNone 
- **Type**: `class`
- **Members**:
    - `content`: A list of strings to be rendered as markdown.
- **Description**: The `ListedRawContentWithNone` class is a subclass of `MdRenderable` designed to handle a list of strings and render them into a markdown format. It provides a method `render_markdown` that takes a document label and outputs a formatted markdown string. If the list is empty, it appends "None" to the markdown output, ensuring that there is always content to display.
- **Inherits From**:
    - MdRenderable

**Methods**

---
#### ListedRawContentWithNone.render_markdown
The `render_markdown` function generates a markdown-formatted string representation of a document label and its associated content list.
- **Inputs**:
    - `doc_label`: A string representing the document label to be formatted in markdown.
- **Control Flow**:
    - Initialize an empty string `output_str`.
    - Append a formatted string with the document label converted from snake_case to spaced string format to `output_str`.
    - Check if the `content` attribute of the class instance is non-empty.
    - If non-empty, iterate over each item in `content` and append it as a bullet point to `output_str`.
    - If empty, append a bullet point with 'None' to `output_str`.
    - Return the `output_str` containing the formatted markdown.
- **Output**:
    - A string containing the markdown-formatted representation of the document label and its content list.



---
### MdRenderable 
- **Type**: `class`
- **Description**: The `MdRenderable` class is an abstract base class that inherits from `BaseModel` and `abc.ABC`, designed to enforce the implementation of a `render_markdown` method in its subclasses. This method is intended to convert content into a markdown string format, with the specific implementation details left to the subclasses.
- **Inherits From**:
    - BaseModel
    - abc.ABC

**Methods**

---
#### MdRenderable.render_markdown
The `render_markdown` function generates a markdown-formatted string based on the content and a given document label.
- **Inputs**:
    - `doc_label`: A string representing the label for the document section to be rendered in markdown format.
- **Control Flow**:
    - The function uses the `snake_case_to_spaced_string` utility to convert the `doc_label` from snake_case to a spaced string format.
    - It then formats the content into a markdown string, with the specific format depending on the class implementing the method.
    - The function returns the formatted markdown string.
- **Output**:
    - A string containing the markdown-formatted content based on the input `doc_label` and the specific class implementation.



---
### NamedContent 
- **Type**: `class`
- **Members**:
    - `name`: A string representing the name of the content.
    - `content`: A string representing the content associated with the name.
- **Description**: The `NamedContent` class is a simple data structure that holds a name and its associated content, both as strings. It inherits from `MdRenderable`, allowing it to render its data in a markdown format using the `render_markdown` method, which formats the name and content into a markdown list item.
- **Inherits From**:
    - MdRenderable

**Methods**

---
#### NamedContent.render_markdown
The `render_markdown` function formats the `name` and `content` attributes of a `NamedContent` instance into a markdown string.
- **Inputs**:
    - `doc_label`: A string representing the document label, which is not used in this function.
- **Control Flow**:
    - The function constructs a markdown string using the `name` and `content` attributes of the `NamedContent` instance.
    - The markdown string is formatted with the `name` enclosed in backticks and followed by the `content`.
- **Output**:
    - A string formatted as a markdown list item with the `name` and `content` of the `NamedContent` instance.



---
### NestedListedRawContent 
- **Type**: `class`
- **Members**:
    - `content`: A nested list of strings representing the content to be rendered.
- **Description**: The `NestedListedRawContent` class is designed to handle and render nested lists of strings into a markdown format. It inherits from the `MdRenderable` class, which requires implementing the `render_markdown` method. This method processes the nested list structure, formatting each sublist as a block and each string within the sublist as an item, and outputs the result as a markdown string. If the content list is empty, it outputs a markdown indicating 'None'.
- **Inherits From**:
    - MdRenderable

**Methods**

---
#### NestedListedRawContent.render_markdown
The `render_markdown` function generates a markdown-formatted string representation of nested list content with a given document label.
- **Inputs**:
    - `doc_label`: A string representing the document label to be used as a heading in the markdown output.
- **Control Flow**:
    - Initialize an empty string `output_str` to build the markdown content.
    - Convert the `doc_label` from snake_case to a spaced string and append it as a bold heading to `output_str`.
    - Check if the `content` attribute of the class instance is non-empty.
    - If `content` is non-empty, iterate over each item in `content`, appending a block number and its subitems to `output_str`.
    - If `content` is empty, append 'None' to `output_str`.
- **Output**:
    - A string containing the markdown representation of the content, formatted with headings and nested lists.



---
### RawContent 
- **Type**: `class`
- **Members**:
    - `content`: A string representing the raw content to be rendered.
- **Description**: The `RawContent` class is a simple implementation of the `MdRenderable` abstract base class, designed to handle and render raw string content as markdown. It contains a single attribute, `content`, which stores the string data, and implements the `render_markdown` method to return the content followed by a newline character. This class is useful for scenarios where raw text needs to be included in markdown documents without additional formatting.
- **Inherits From**:
    - MdRenderable

**Methods**

---
#### RawContent.render_markdown
The `render_markdown` function returns the content of the `RawContent` class as a string with a newline appended.
- **Inputs**:
    - `doc_label`: A string representing the document label, which is not used in this function.
- **Control Flow**:
    - The function directly returns the `content` attribute of the `RawContent` instance followed by a newline character.
- **Output**:
    - A string consisting of the `content` attribute followed by a newline character.



---
### VariableData 
- **Type**: `class`
- **Members**:
    - `type`: Specifies the type of the variable with backtick content.
    - `description`: Provides a raw content description of the variable.
    - `use`: Describes the usage of the variable with raw content.
- **Description**: The `VariableData` class is a specialized subclass of `IrData` designed to encapsulate information about a variable, including its type, description, and usage. It provides a class method `default_instance` to create a default instance with empty content for each field. This class is part of a larger framework for handling and rendering data structures in a markdown format.
- **Inherits From**:
    - IrData

**Methods**

---
#### VariableData.default_instance
The `default_instance` function creates and returns a default instance of the class with specific fields initialized to empty content.
- **Inputs**:
    - `cls`: The class for which a default instance is to be created.
- **Control Flow**:
    - The function is a class method that takes a class (`cls`) as an argument.
    - It returns an instance of the class (`cls`) with specific fields (`type`, `description`, `use`) initialized using `FieldNameWithBackTickContent` and `FieldNameWithRawContent` classes, all with empty content.
- **Output**:
    - An instance of the class (`cls`) with default field values.



# Functions

---
### compute_num_workers 
The function computes the number of workers needed based on the number of symbols, constrained by maximum limits.
- **Inputs**:
    - `num_symbols`: The total number of symbols that need to be processed.
- **Control Flow**:
    - Calculate the ceiling of the division of num_symbols by MAX_SYMBOLS_PER_WORKER to determine the minimum number of workers needed based on symbol count.
    - Use the min function to ensure the number of workers does not exceed MAX_WORKERS_FOR_SYMBOLS.
- **Output**:
    - Returns the minimum number of workers required, constrained by the maximum number of workers allowed.


---
### snake_case_to_spaced_string 
The function converts a snake_case string to a spaced and capitalized string.
- **Inputs**:
    - `snake_case`: A string in snake_case format, where words are separated by underscores.
- **Control Flow**:
    - The input string is split into a list of words using the underscore ('_') as the delimiter.
    - Each word in the list is capitalized.
    - The capitalized words are joined together with a space (' ') to form the final string.
- **Output**:
    - A string where each word from the input is capitalized and separated by spaces.


