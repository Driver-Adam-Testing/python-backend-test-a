# Purpose
This Python file is an Alembic migration script designed to modify the database schema for a table named `document_sources`. The primary purpose of this script is to reset the primary key of the `document_sources` table and ensure data integrity by removing entries with null values in critical columns (`source_node_id` and `page_node_id`) and eliminating duplicate entries based on these columns. The script achieves this by first executing SQL commands to delete unwanted records and then altering the table's primary key to be a composite of `source_node_id` and `page_node_id`. Additionally, it adjusts the nullability constraints of several columns, making `source_node_id` and `page_node_id` non-nullable while allowing other columns to be nullable.

The script is structured with two main functions: `upgrade()` and `downgrade()`. The `upgrade()` function implements the changes to the database schema, while the `downgrade()` function reverses these changes, restoring the previous schema state. This migration script is part of a broader database version control system managed by Alembic, which is a lightweight database migration tool for SQLAlchemy. The script includes metadata such as revision identifiers to track changes and dependencies between different migration scripts, ensuring that database schema changes are applied in a controlled and sequential manner.
# Imports and Dependencies

---
- `sqlalchemy`
- `alembic`


# Global Variables

---
### branch_labels 
- **Type**: `NoneType`
- **Description**: The variable `branch_labels` is a global variable set to `None`. It is part of the Alembic migration script metadata, which is used to define characteristics of the migration, such as revision identifiers and dependencies.
- **Use**: This variable is used to specify branch labels for the migration, but in this case, it is not utilized as it is set to `None`.


---
### depends_on 
- **Type**: `NoneType`
- **Description**: The `depends_on` variable is a global variable set to `None`. It is part of the Alembic migration script metadata, which typically includes information about dependencies between migration scripts.
- **Use**: This variable is used to indicate that the current migration script does not depend on any other migration script.


---
### down_revision 
- **Type**: `str`
- **Description**: The `down_revision` variable is a string that holds the identifier of the previous database schema revision in an Alembic migration script. It is used to establish a link between the current revision and its predecessor, allowing Alembic to maintain a linear history of database changes.
- **Use**: This variable is used by Alembic to determine the order of migrations and to apply them in the correct sequence.


---
### revision 
- **Type**: `str`
- **Description**: The `revision` variable is a string that uniquely identifies the current database schema version in the context of Alembic migrations. It is used to track changes and manage the versioning of the database schema over time.
- **Use**: This variable is used by Alembic to apply or rollback database migrations to the specific schema version identified by this revision ID.


# Functions

---
### downgrade 
The `downgrade` function modifies the schema of the `document_sources` table by altering the nullability of several columns.
- **Inputs**:
    - None
- **Control Flow**:
    - The function begins by altering the `page_node_id` column in the `document_sources` table to allow null values.
    - Next, it alters the `source_node_id` column to allow null values as well.
    - The `source_id` column is then altered to disallow null values.
    - The `include` column is also altered to disallow null values.
    - Finally, the `document_id` column is altered to disallow null values.
- **Output**:
    - The function does not return any value; it performs schema alterations on the database.


---
### upgrade 
The `upgrade` function modifies the `document_sources` table by cleaning up invalid entries, removing duplicates, resetting the primary key, and altering column constraints.
- **Inputs**:
    - None
- **Control Flow**:
    - Execute a SQL command to delete rows from `document_sources` where `source_node_id` or `page_node_id` is NULL.
    - Execute a SQL command to delete duplicate rows from `document_sources` based on `source_node_id` and `page_node_id`.
    - Drop the existing primary key constraint on the `document_sources` table.
    - Create a new primary key constraint on the `document_sources` table using `source_node_id` and `page_node_id`.
    - Alter the `document_id`, `include`, and `source_id` columns to be nullable.
    - Alter the `source_node_id` and `page_node_id` columns to be non-nullable.
- **Output**:
    - The function does not return any value; it performs database schema modifications.


