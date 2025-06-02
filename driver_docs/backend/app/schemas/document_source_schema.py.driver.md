# Purpose
This code defines a Pydantic model named `DocumentSourceCreate`, which is used for data validation and serialization in Python applications. The model includes three fields: `document_id` and `source_id`, both of which are UUIDs, and `include`, a boolean. This code provides narrow functionality, specifically for creating and validating instances of `DocumentSourceCreate` with the specified fields. It is a short script that leverages Pydantic's capabilities to ensure that the data conforms to the expected types and structure, which is particularly useful in applications that require strict data validation, such as APIs or data processing pipelines.
# Imports and Dependencies

---
- `typing`
- `uuid`
- `pydantic`


# Classes

---
### DocumentSourceCreate 
- **Type**: `class`
- **Members**:
    - `document_id`: A UUID representing the unique identifier of the document.
    - `source_id`: A UUID representing the unique identifier of the source.
    - `include`: A boolean indicating whether the source should be included.
- **Description**: The `DocumentSourceCreate` class is a Pydantic model used to define the structure of data required to create a link between a document and a source. It includes fields for the document's unique identifier, the source's unique identifier, and a boolean flag to indicate if the source should be included. This class ensures that the data conforms to the specified types and constraints, leveraging Pydantic's data validation capabilities.
- **Inherits From**:
    - BaseModel


