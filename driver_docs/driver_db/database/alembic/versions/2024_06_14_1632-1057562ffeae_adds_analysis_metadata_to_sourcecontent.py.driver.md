# Purpose
This source code file is an Alembic migration script designed to modify a database schema by adding a new column to an existing table. Specifically, it adds an `analysis_metadata` column of type JSONB to the `source_contents` table, allowing for the storage of JSON data with optional text representation. The script provides narrow functionality, focusing solely on this schema change, and includes both an `upgrade` function to apply the change and a `downgrade` function to revert it. The use of Alembic, a database migration tool for SQLAlchemy, indicates that this script is part of a version-controlled database schema management process.
# Imports and Dependencies

---
- `alembic.op`
- `sqlalchemy`
- `sqlmodel.sql.sqltypes`
- `sqlalchemy.dialects.postgresql`


# Global Variables

---
### branch_labels 
- **Type**: `NoneType`
- **Description**: The `branch_labels` variable is a global variable set to `None`. It is part of the Alembic migration script metadata, which typically includes identifiers for the migration such as revision IDs and dependencies.
- **Use**: This variable is used to define branch labels for the migration script, but in this case, it is not utilized as it is set to `None`.


---
### depends_on 
- **Type**: `NoneType`
- **Description**: The `depends_on` variable is a global variable set to `None`. It is part of the Alembic migration script metadata, which typically includes information about dependencies between migration scripts.
- **Use**: This variable is used to indicate that the current migration script does not depend on any other migration scripts.


---
### down_revision 
- **Type**: `str`
- **Description**: The `down_revision` variable is a string that holds the identifier of the previous database schema revision in an Alembic migration script. It is used to establish a linear sequence of migrations, allowing Alembic to determine the order in which migrations should be applied.
- **Use**: This variable is used by Alembic to track and apply database schema changes in the correct order.


---
### revision 
- **Type**: `str`
- **Description**: The `revision` variable is a string that uniquely identifies the current database migration script. It is used by Alembic, a database migration tool, to track and apply changes to the database schema.
- **Use**: This variable is used by Alembic to identify the specific migration script when applying or rolling back database schema changes.


# Functions

---
### downgrade 
The `downgrade` function removes the 'analysis_metadata' column from the 'source_contents' table in the database.
- **Inputs**:
    - None
- **Control Flow**:
    - The function calls `op.drop_column` to remove the 'analysis_metadata' column from the 'source_contents' table.
- **Output**:
    - The function does not return any value; it performs a database schema modification.


---
### upgrade 
The `upgrade` function adds a new column named 'analysis_metadata' of type JSONB to the 'source_contents' table in the database.
- **Inputs**:
    - None
- **Control Flow**:
    - The function uses Alembic's `op.add_column` method to add a new column to an existing table.
    - The new column 'analysis_metadata' is of type JSONB, which allows for storing JSON data, and is nullable.
- **Output**:
    - The function does not return any output; it performs a database schema modification.


