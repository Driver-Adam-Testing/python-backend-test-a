# Purpose
This Python file is an Alembic migration script designed to manage database schema changes specifically related to content types in a database. The script defines two primary functions, `upgrade()` and `downgrade()`, which are used to apply and revert changes to the database schema, respectively. The `upgrade()` function checks for the existence of certain content types in the `derived_content_types` table and inserts new types if they are not already present. Conversely, the `downgrade()` function removes these content types from the table, effectively reversing the changes made by the `upgrade()` function. This script is part of a version-controlled database migration system, as indicated by the use of Alembic, a database migration tool for SQLAlchemy.

The script is structured to ensure that only new content types are added to the database, preventing duplication. It uses raw SQL queries executed through SQLAlchemy's text interface to interact with the database. The migration is identified by a unique revision ID (`37da9f662cf0`) and is linked to a previous migration (`2f79ea9294a7`), ensuring a sequential and organized application of database changes. This script is not intended to be a standalone application but rather a component of a larger system that manages database schema evolution, providing a narrow and specific functionality within the context of database migrations.
# Imports and Dependencies

---
- `sqlalchemy`
- `alembic`


# Global Variables

---
### branch_labels 
- **Type**: `NoneType`
- **Description**: The `branch_labels` variable is a global variable set to `None`. It is part of the Alembic migration script metadata, which typically includes identifiers for branching in database schema versions.
- **Use**: This variable is used to indicate that there are no branch labels associated with this particular database migration script.


---
### content_types 
- **Type**: `list`
- **Description**: The `content_types` variable is a list of strings, each representing a specific type of content that can be derived from a PDF. These types include visual summaries, text summaries, image summaries, extracted text, and extracted tables.
- **Use**: This variable is used to determine which content types need to be inserted into or deleted from the `derived_content_types` table during database migrations.


---
### depends_on 
- **Type**: `NoneType`
- **Description**: The `depends_on` variable is a global variable set to `None`. It is part of the Alembic migration script metadata, which typically indicates dependencies on other migrations.
- **Use**: This variable is used to specify that the current migration does not depend on any other migrations.


---
### down_revision 
- **Type**: `str`
- **Description**: The `down_revision` variable is a string that holds the identifier of the previous database schema revision in a sequence of migrations managed by Alembic. It is used to establish a link between the current revision and its predecessor, allowing Alembic to maintain a coherent migration history.
- **Use**: This variable is used by Alembic to determine the order of database migrations and to apply them in the correct sequence.


---
### revision 
- **Type**: `str`
- **Description**: The `revision` variable is a string that serves as a unique identifier for a specific database schema migration in Alembic. It is used to track the version of the database schema and ensure that migrations are applied in the correct order.
- **Use**: This variable is used by Alembic to identify and apply the correct database migration script.


# Functions

---
### downgrade 
The `downgrade` function removes specific content types from the `derived_content_types` table in the database.
- **Inputs**:
    - None
- **Control Flow**:
    - The function constructs a SQL DELETE query to remove entries from the `derived_content_types` table where the `type_name` matches any of the predefined `content_types`.
    - It uses a list comprehension to format each `type_name` in `content_types` as a string suitable for inclusion in the SQL query.
    - The function retrieves a database connection using `op.get_bind()`.
    - It executes the constructed SQL DELETE query using the connection.
- **Output**:
    - The function does not return any value; it performs a database operation to delete specific rows.


---
### upgrade 
The `upgrade` function inserts new content types into the `derived_content_types` table if they do not already exist.
- **Inputs**:
    - None
- **Control Flow**:
    - Retrieve a database connection using `op.get_bind()`.
    - Execute a SQL query to select all existing type names from the `derived_content_types` table.
    - Store the existing type names in a set called `existing_types`.
    - Create a list `new_types` containing type names from `content_types` that are not in `existing_types`.
    - If `new_types` is not empty, construct an SQL insert statement to add these new types to the `derived_content_types` table.
    - Execute the constructed SQL insert statement using the database connection.
- **Output**:
    - The function does not return any value; it performs database operations to update the `derived_content_types` table.


