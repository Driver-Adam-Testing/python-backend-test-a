# Purpose
This Python file is an Alembic migration script designed to modify a database schema by adding timestamp columns to existing tables. Specifically, it introduces `created_at` and `updated_at` columns to the `chunk`, `contentmetadata`, and `contentprocessingsession` tables. These columns are of type `DateTime` with timezone support and are initially nullable. The purpose of these columns is to track the creation and last update times of records within these tables, which is a common practice for maintaining data integrity and facilitating auditing processes.

The script defines two primary functions: `upgrade()` and `downgrade()`. The `upgrade()` function is responsible for applying the schema changes by adding the new columns, while the `downgrade()` function reverses these changes by removing the columns, allowing for easy rollback if necessary. The script includes metadata such as `revision`, `down_revision`, and other identifiers that Alembic uses to manage the sequence and dependencies of database migrations. This file is part of a broader database migration system and is intended to be executed within the context of an Alembic-managed project, rather than being a standalone script or library.
# Imports and Dependencies

---
- `typing`
- `sqlalchemy`
- `alembic`


# Global Variables

---
### branch_labels 
- **Type**: `Union[str, Sequence[str], None]`
- **Description**: The `branch_labels` variable is a global variable used in Alembic migration scripts to specify labels for a particular branch of the database schema. It can be a string, a sequence of strings, or None, indicating that no specific branch labels are assigned.
- **Use**: This variable is used to define branch labels for the migration, which can help in organizing and managing different branches of database schema changes.


---
### depends_on 
- **Type**: `Union[str, Sequence[str], None]`
- **Description**: The `depends_on` variable is a global variable used in Alembic migration scripts to specify dependencies on other migrations. It can be a string representing a single revision ID, a sequence of revision IDs, or None if there are no dependencies.
- **Use**: This variable is used to define the migration dependencies for the current migration script.


---
### down_revision 
- **Type**: `Union[str, None]`
- **Description**: The `down_revision` variable is a global variable used in Alembic migration scripts to specify the identifier of the previous revision in the migration chain. It is set to a string representing the revision ID of the immediate predecessor of the current migration, or `None` if there is no predecessor.
- **Use**: This variable is used by Alembic to determine the order of migrations and to apply them in the correct sequence.


---
### revision 
- **Type**: `str`
- **Description**: The `revision` variable is a string that uniquely identifies the current database schema migration version in Alembic. It is used to track changes and manage the versioning of the database schema.
- **Use**: This variable is used by Alembic to apply or rollback database migrations to the specific version identified by this revision ID.


# Functions

---
### downgrade 
The `downgrade` function removes the 'created_at' and 'updated_at' columns from the 'chunk', 'contentmetadata', and 'contentprocessingsession' tables.
- **Inputs**:
    - None
- **Control Flow**:
    - The function begins by calling `op.drop_column` to remove the 'updated_at' column from the 'contentprocessingsession' table.
    - It then removes the 'created_at' column from the 'contentprocessingsession' table using `op.drop_column`.
    - The function proceeds to remove the 'updated_at' column from the 'contentmetadata' table.
    - Next, it removes the 'created_at' column from the 'contentmetadata' table.
    - The function continues by removing the 'updated_at' column from the 'chunk' table.
    - Finally, it removes the 'created_at' column from the 'chunk' table.
- **Output**:
    - The function does not return any value; it performs schema changes on the database.


---
### upgrade 
The `upgrade` function adds 'created_at' and 'updated_at' timestamp columns to the 'chunk', 'contentmetadata', and 'contentprocessingsession' tables in a database schema using Alembic.
- **Inputs**:
    - None
- **Control Flow**:
    - The function begins by adding a 'created_at' column to the 'chunk' table with a DateTime type that supports timezone and allows null values.
    - It then adds an 'updated_at' column to the 'chunk' table with similar properties.
    - The function proceeds to add 'created_at' and 'updated_at' columns to the 'contentmetadata' table, both with DateTime type, timezone support, and nullable.
    - Similarly, 'created_at' and 'updated_at' columns are added to the 'contentprocessingsession' table with the same properties.
- **Output**:
    - The function does not return any value; it performs schema modifications directly on the database.


