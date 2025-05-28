# Purpose
This Python code file is designed to enhance SQLAlchemy/SQLModel queries with advanced filtering, sorting, and pagination capabilities, primarily for use in web applications built with FastAPI. The file defines a `SortDirection` enumeration to specify sorting order and a `PaginationQueryParams` class to encapsulate pagination parameters such as limit, offset, sorting field, and direction. The `get_pagination_params` function, along with the `Pagination` type alias, integrates these parameters into FastAPI's dependency injection system, allowing for seamless retrieval of pagination settings from HTTP requests.

The core functionality is provided by two functions: `apply_filters_to_query` and `apply_sorting_to_query`. `apply_filters_to_query` allows for dynamic filtering of SQL queries based on a dictionary of filter criteria, supporting complex operations like JSONB column indexing and relationship-based filtering using dot notation. It includes a robust mechanism for handling various SQL operators and validates filter keys to ensure they correspond to valid model attributes. `apply_sorting_to_query` adds sorting and pagination to queries, supporting sorting on both regular and JSONB columns, and handles relationship paths for sorting fields. Together, these components form a cohesive module that can be integrated into FastAPI applications to provide flexible and efficient query customization based on client requests.
# Imports and Dependencies

---
- `enum`
- `typing`
- `fastapi`
- `sqlalchemy.dialects.postgresql`
- `sqlalchemy.orm`
- `sqlalchemy.orm.attributes`
- `sqlalchemy.sql`
- `sqlmodel`


# Global Variables

---
### ASC
- **Type**: `str`
- **Description**: `ASC` is a member of the `SortDirection` enumeration, representing the ascending order for sorting operations. It is defined as a string with the value "ASC".
- **Use**: This variable is used to specify the ascending order when sorting query results in the `apply_sorting_to_query` function.


---
### DESC
- **Type**: `Enum`
- **Description**: `DESC` is a member of the `SortDirection` enumeration, which is a subclass of `str` and `Enum`. It represents the descending sort direction for ordering query results.
- **Use**: This variable is used to specify the descending order when sorting query results in the `apply_sorting_to_query` function.


---
### Pagination
- **Type**: `Annotated[PaginationQueryParams, Depends(get_pagination_params)]`
- **Description**: The `Pagination` variable is an annotated type that combines the `PaginationQueryParams` class with a dependency injection using FastAPI's `Depends` function. This setup allows for automatic extraction and validation of pagination-related query parameters from incoming HTTP requests.
- **Use**: This variable is used to manage pagination parameters in API requests, facilitating the retrieval of paginated data from a database.


# Classes

---
### PaginationQueryParams
- **Type**: `class`
- **Members**:
    - `limit`: The maximum number of items to return, defaulting to 10.
    - `offset`: The number of items to skip before starting to collect the result set, defaulting to 0.
    - `sort_by`: The field name to sort the results by, defaulting to None.
    - `sort_direction`: The direction of sorting, either ascending or descending, defaulting to descending.
- **Description**: The `PaginationQueryParams` class is designed to encapsulate pagination and sorting parameters for database queries. It provides default values for the number of items to return (`limit`), the starting point of the result set (`offset`), the field to sort by (`sort_by`), and the direction of sorting (`sort_direction`). This class is typically used in conjunction with query functions to apply pagination and sorting to SQL queries.

**Methods**

---
#### PaginationQueryParams.__init__
The `__init__` function initializes an instance of the `PaginationQueryParams` class with default or provided pagination and sorting parameters.
- **Inputs**:
    - `limit`: An integer specifying the maximum number of items to return, defaulting to 10.
    - `offset`: An integer specifying the number of items to skip before starting to collect the result set, defaulting to 0.
    - `sort_by`: A string or None specifying the field by which to sort the results, defaulting to None.
    - `sort_direction`: An instance of `SortDirection` enum specifying the direction of sorting, defaulting to `SortDirection.DESC`.
- **Control Flow**:
    - Assigns the provided or default value of `limit` to the instance variable `self.limit`.
    - Assigns the provided or default value of `offset` to the instance variable `self.offset`.
    - Assigns the provided or default value of `sort_by` to the instance variable `self.sort_by`.
    - Assigns the provided or default value of `sort_direction` to the instance variable `self.sort_direction`.
- **Output**:
    - The function does not return any value; it initializes the instance variables of the class.



---
### SortDirection
- **Type**: `class`
- **Members**:
    - `ASC`: Represents ascending sort direction.
    - `DESC`: Represents descending sort direction.
- **Description**: The `SortDirection` class is an enumeration that inherits from both `str` and `Enum`, providing two possible values, `ASC` and `DESC`, to represent ascending and descending sort directions, respectively. This class is used to specify the direction of sorting operations in queries, ensuring that only valid sort directions are used.
- **Inherits From**:
    - str
    - Enum


# Functions

---
### apply_filters_to_query
The `apply_filters_to_query` function applies specified filters to a SQLAlchemy/SQLModel select query using a dictionary of filter keys and values, supporting various operators and handling relationships and JSONB columns.
- **Inputs**:
    - `query`: A SQLAlchemy/SQLModel Select object representing the initial query to which filters will be applied.
    - `filters`: A dictionary where keys are filter expressions (potentially using double-underscore syntax for operators) and values are the corresponding filter values.
    - `model`: An SQLModel class representing the database model on which the query is based.
- **Control Flow**:
    - Initialize a dictionary `OPERATORS` mapping operator strings to lambda functions for SQLAlchemy expressions.
    - Iterate over each key-value pair in the `filters` dictionary.
    - Split each filter key on '__' to separate the field name and operator.
    - Determine the operator to use, defaulting to 'in' for comma-separated strings or 'default' otherwise.
    - Split the field name on '.' to handle potential relationships or JSONB columns.
    - Check if the operator is valid; raise an HTTPException if not.
    - Convert comma-separated string values to lists for 'in'/'nin' operators.
    - For single-part field names, check if the attribute exists on the model and is not a relationship; apply the filter using the appropriate operator.
    - For multi-part field names, recursively apply filters to handle relationships or JSONB columns, raising HTTPExceptions for invalid paths.
    - Return the modified query with all applicable filters applied.
- **Output**:
    - A modified SQLAlchemy/SQLModel Select object with the specified filters applied.


---
### apply_recursive_filter
The `apply_recursive_filter` function applies a filter operation recursively on a model's attributes, supporting JSONB columns and relationships.
- **Inputs**:
    - `model`: The SQLAlchemy model on which the filter is to be applied.
    - `parts`: A list of strings representing the path to the attribute or column, potentially including relationships or JSONB keys.
    - `value`: The value to be used in the filter operation.
    - `op`: A string representing the operation to be applied, such as 'eq', 'lt', 'gt', etc.
- **Control Flow**:
    - Check if the `parts` list has only one element; if so, apply the operator directly to the column specified by that element.
    - If the column specified by the first element of `parts` is not found on the model, raise an HTTPException with a 400 status code.
    - If the column is a JSONB type, iterate over the remaining parts to index into the JSON and apply the operator to the resulting expression.
    - If the column is a relationship, recursively call `apply_recursive_filter` on the related model with the remaining parts, and apply the operator using `.any()` or `.has()` depending on whether the relationship is a list.
- **Output**:
    - The function returns a filter expression that can be used in a SQLAlchemy query, or raises an HTTPException if an error occurs.


---
### apply_sorting_to_query
The function applies sorting and pagination to a SQLAlchemy/SQLModel 'select' query, supporting sorting on JSONB columns using dot notation.
- **Inputs**:
    - `query`: A SQLAlchemy/SQLModel 'select' query object to which sorting and pagination will be applied.
    - `pagination`: An instance of PaginationQueryParams containing sorting and pagination parameters such as sort_by, sort_direction, limit, and offset.
    - `model`: A SQLModel class representing the database model, used to validate and apply sorting fields.
- **Control Flow**:
    - Check if pagination.sort_by is provided; if not, skip sorting logic.
    - Split the sort_by field by '.' to handle dot notation for JSONB or relationships.
    - If the sort field is a single part, verify it exists on the model; otherwise, raise an HTTPException for invalid fields.
    - For multi-part sort fields, iterate through parts to navigate relationships, joining tables as necessary, and validate each part; raise HTTPException for invalid paths or relationships.
    - Determine the final sort column from the last part of the sort field and validate its existence on the current model.
    - Apply sorting to the query based on the sort direction (ASC or DESC), optionally including the model's id for distinct ordering if available.
    - Apply pagination to the query using the limit and offset from the pagination parameters.
    - Return the modified query.
- **Output**:
    - A modified SQLAlchemy/SQLModel 'select' query with applied sorting and pagination.


---
### get_pagination_params
The `get_pagination_params` function retrieves pagination parameters from a dependency injection in a FastAPI application.
- **Inputs**:
    - `params`: An instance of `PaginationQueryParams` which is injected as a dependency using FastAPI's `Depends`.
- **Control Flow**:
    - The function takes a single argument `params` which is expected to be provided by FastAPI's dependency injection system.
    - It directly returns the `params` argument without any modification.
- **Output**:
    - The function returns the `PaginationQueryParams` instance that was passed to it as an argument.


