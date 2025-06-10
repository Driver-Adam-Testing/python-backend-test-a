# Purpose
This Python code defines a set of data models using the Pydantic library, which are intended for use in a system that manages tags and collections, likely within a web application. The code provides narrow functionality, focusing specifically on the validation and structuring of input and output data related to tags. It includes several Pydantic `BaseModel` classes, such as `ListTagsInput`, `TagInputBase`, `NewTagInput`, `EditTagInput`, `CollectionSourceInput`, `ListTagsResults`, and `ListTagContentsResults`, each serving a specific purpose in handling tag-related data. The models enforce data validation rules, such as stripping whitespace and ensuring valid hex color formats, to maintain data integrity. This file is a crucial part of the application's data handling layer, ensuring that the data conforms to expected formats before being processed or stored.
# Imports and Dependencies

---
- `typing`
- `database.models_v1`
- `pydantic`
- `app.schemas.content_schema`


# Global Variables

---
### TagType 
- **Type**: `Literal`
- **Description**: `TagType` is a type alias defined using Python's `Literal` type, which restricts the value to be either 'tag' or 'collection'. This ensures that any variable of type `TagType` can only take one of these two string values.
- **Use**: This variable is used to enforce type safety and restrict the values of the `type` field in various data models, such as `ListTagsInput`, `NewTagInput`, and `EditTagInput`.


---
### hex_color 
- **Type**: `str`
- **Description**: The `hex_color` variable is a string that represents a color in hexadecimal format, typically used in web design and development to specify colors. It is expected to be a string starting with a '#' followed by six hexadecimal digits, which represent the red, green, and blue components of the color.
- **Use**: This variable is used to store and validate the color information for tags, ensuring it adheres to the standard hex color format.


---
### name 
- **Type**: `str`
- **Description**: The `name` variable is a string that represents the name of a tag or collection. It is used in multiple classes, such as `ListTagsInput`, `TagInputBase`, and `EditTagInput`, where it can be either a required or optional field.
- **Use**: This variable is used to store and validate the name of a tag or collection in various input models.


# Classes

---
### CollectionSourceInput 
- **Type**: `class`
- **Members**:
    - `include`: A boolean indicating whether to include the collection source.
- **Description**: The `CollectionSourceInput` class is a simple data model that inherits from Pydantic's `BaseModel`. It contains a single boolean field, `include`, which is used to specify whether a particular collection source should be included or not. This class is likely used as part of a larger system to manage or filter collections based on user input or configuration.
- **Inherits From**:
    - BaseModel


---
### EditTagInput 
- **Type**: `class`
- **Members**:
    - `name`: Optional string representing the name of the tag to be edited.
    - `hex_color`: Optional string representing the hex color of the tag to be edited.
- **Description**: The EditTagInput class is a subclass of TagInputBase, designed to handle the input for editing an existing tag. It allows for optional modification of the tag's name and hex color, inheriting validation methods from its parent class to ensure proper formatting and whitespace handling.
- **Inherits From**:
    - TagInputBase


---
### ListTagContentsResults 
- **Type**: `class`
- **Members**:
    - `tag`: Represents the tag associated with the content results.
    - `results`: A list of content results associated with the tag.
    - `offset`: Indicates the starting point of the results in the list.
    - `limit`: Specifies the maximum number of results to return.
    - `count`: The total number of results available.
- **Description**: The `ListTagContentsResults` class is a data model that encapsulates the results of a query for content associated with a specific tag. It includes the tag itself, a list of content results, and pagination information such as offset, limit, and total count of results. This class is useful for managing and returning structured data in applications that handle tagged content.
- **Inherits From**:
    - BaseModel


---
### ListTagsInput 
- **Type**: `class`
- **Members**:
    - `name`: Optional string representing the name of the tag.
    - `type`: Optional TagType indicating the type of tag, either 'tag' or 'collection'.
    - `limit`: Integer specifying the maximum number of tags to return.
    - `offset`: Integer specifying the starting point for the list of tags to return.
- **Description**: The ListTagsInput class is a data model used to specify the parameters for listing tags, including optional filters for the tag name and type, as well as pagination controls through limit and offset values. It inherits from BaseModel, which provides validation and serialization capabilities.
- **Inherits From**:
    - BaseModel


---
### ListTagsResults 
- **Type**: `class`
- **Members**:
    - `results`: A list of Tag objects representing the tags retrieved.
    - `offset`: An integer indicating the starting point of the results in the dataset.
    - `limit`: An integer specifying the maximum number of results to return.
    - `count`: An integer representing the total number of tags available.
- **Description**: The `ListTagsResults` class is a data model that encapsulates the results of a tag listing operation. It includes a list of `Tag` objects, along with pagination information such as the offset, limit, and total count of tags. This class is used to structure the response data when querying for tags, providing both the data and the context needed for pagination.
- **Inherits From**:
    - BaseModel


---
### NewTagInput 
- **Type**: `class`
- **Members**:
    - `type`: Specifies the type of the tag, which can be either 'tag' or 'collection'.
- **Description**: The `NewTagInput` class is a specialized form of `TagInputBase` that adds a `type` attribute to specify the kind of tag being created, either as a 'tag' or a 'collection'. It inherits validation methods from `TagInputBase` to ensure that the `name` and `hex_color` fields are properly formatted.
- **Inherits From**:
    - TagInputBase


---
### TagInputBase 
- **Type**: `class`
- **Members**:
    - `name`: A string representing the name of the tag.
    - `hex_color`: A string representing the hex color code of the tag.
- **Description**: The `TagInputBase` class is a Pydantic model that serves as a base class for handling tag input data, specifically focusing on the name and hex color attributes. It includes validators to strip whitespace from both fields and to ensure that the hex color is in a valid format, starting with a '#' and followed by six hexadecimal characters.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### TagInputBase.strip_whitespace
The `strip_whitespace` function removes leading and trailing whitespace from a string if the input is a string, otherwise it returns the input unchanged.
- **Inputs**:
    - `cls`: The class reference, typically used in class methods to access class attributes or other methods.
    - `value`: The input value which is checked if it is a string to potentially strip whitespace from it.
- **Control Flow**:
    - Check if the input `value` is an instance of `str`.
    - If `value` is a string, return the result of `value.strip()`, which removes leading and trailing whitespace.
    - If `value` is not a string, return the `value` unchanged.
- **Output**:
    - The function returns the input string with leading and trailing whitespace removed if it is a string, otherwise it returns the input value unchanged.


---
#### TagInputBase.validate_hex_color
The `validate_hex_color` function checks if a given string is a valid hexadecimal color code and raises an error if it is not.
- **Inputs**:
    - `cls`: The class reference, typically passed automatically by the class method decorator.
    - `value`: A string representing the hex color code to be validated.
- **Control Flow**:
    - The function first checks if the string starts with a '#' character.
    - It then verifies that the length of the string is exactly 7 characters.
    - The function checks that all characters following the '#' are valid hexadecimal digits (0-9, A-F, a-f).
    - If any of these conditions are not met, a `ValueError` is raised with the message 'Invalid hex color format'.
    - If all conditions are satisfied, the function returns the original value.
- **Output**:
    - The function returns the validated hex color string if it is in the correct format, otherwise it raises a `ValueError`.



