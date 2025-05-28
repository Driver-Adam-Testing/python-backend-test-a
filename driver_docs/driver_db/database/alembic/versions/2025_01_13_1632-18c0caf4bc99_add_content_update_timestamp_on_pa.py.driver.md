# Purpose
This Python script is an Alembic migration file designed to modify a database schema by adding a new column to an existing table. Specifically, it adds a `related_content_last_updated` column of type `DateTime` with timezone support to the `v2_primary_asset` table. The purpose of this column is to track the last update timestamp of related content for each primary asset. The script includes an `upgrade` function that not only adds the column but also populates it with initial data. It sets a default timestamp for rows where the new column is initially null and updates it with the latest content update timestamp derived from related tables. This ensures that the new column is immediately useful for tracking content updates.

The script also defines a `downgrade` function, which serves as a rollback mechanism by removing the `related_content_last_updated` column from the `v2_primary_asset` table. This migration file is part of a broader database versioning system managed by Alembic, which is a lightweight database migration tool for SQLAlchemy. The file includes metadata such as revision identifiers to track changes and dependencies between different migration scripts. This ensures that the database schema can be consistently upgraded or downgraded across different environments.
# Imports and Dependencies

---
- `textwrap`
- `sqlalchemy`
- `alembic`


# Global Variables

---
### branch_labels 
- **Type**: `NoneType`
- **Description**: The `branch_labels` variable is a global variable set to `None`. It is part of the Alembic migration script metadata, which typically includes identifiers for the migration such as revision ID and dependencies.
- **Use**: This variable is used to define branch labels for the migration, but in this case, it is not utilized as it is set to `None`.


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
- **Description**: The `revision` variable is a string that holds the unique identifier for the current database migration script. It is used by Alembic, a database migration tool for SQLAlchemy, to track and apply changes to the database schema.
- **Use**: This variable is used by Alembic to identify the specific migration script when applying or rolling back database schema changes.


# Functions

---
### downgrade 
The `downgrade` function removes the 'related_content_last_updated' column from the 'v2_primary_asset' table.
- **Inputs**:
    - None
- **Control Flow**:
    - The function calls `op.drop_column` with the table name 'v2_primary_asset' and the column name 'related_content_last_updated'.
- **Output**:
    - The function does not return any value (returns None).


---
### upgrade 
The `upgrade` function adds a new column to the `v2_primary_asset` table and updates it with timestamps based on related content updates.
- **Inputs**:
    - None
- **Control Flow**:
    - The function begins by adding a new column named `related_content_last_updated` to the `v2_primary_asset` table, which is of type `DateTime` with timezone support and allows null values.
    - It then executes a SQL script to update the `related_content_last_updated` column for all rows where it is currently null, setting it to a default timestamp of '1970-01-01 00:00:00+00'.
    - A common table expression (CTE) named `latest_content_updates` is created to find the latest content update timestamp for each primary asset by joining `v2_primary_asset`, `v2_version`, `v2_node`, and `derived_contents` tables.
    - The `v2_primary_asset` table is then updated with the latest content update timestamps from the CTE, but only for rows where the new timestamp is more recent than the existing value in `related_content_last_updated`.
- **Output**:
    - The function does not return any value; it performs database schema and data updates.


