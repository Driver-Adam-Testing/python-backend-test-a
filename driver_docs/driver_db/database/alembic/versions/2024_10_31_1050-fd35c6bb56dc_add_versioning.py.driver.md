# Purpose
This Python file is an Alembic migration script designed to modify a database schema by adding versioning capabilities. It introduces two new tables, `inspection_versions` and `inspectorrun`, which are essential for tracking different versions of inspections and their execution runs. The `inspection_versions` table includes columns for storing unique identifiers, version information, display names, and timestamps for creation and updates, along with a self-referential foreign key to track previous versions. The `inspectorrun` table links to `inspection_versions` through a foreign key, allowing each run to be associated with a specific version of an inspection. Additionally, the script modifies the `derived_contents` table by adding a new column, `version_id`, and creates an index and a foreign key relationship to the `inspection_versions` table.

The script is structured to be used with Alembic, a database migration tool for SQLAlchemy, and includes both `upgrade` and `downgrade` functions. The `upgrade` function applies the changes to the database schema, while the `downgrade` function reverses them, ensuring that the database can be rolled back to its previous state if necessary. This migration script is a crucial part of a version control system for database records, enabling the tracking and management of changes over time, which is particularly useful in applications where historical data integrity and auditability are important.
# Imports and Dependencies

---
- `sqlalchemy`
- `sqlmodel.sql.sqltypes`
- `alembic.op`


# Global Variables

---
### branch_labels 
- **Type**: `NoneType`
- **Description**: The `branch_labels` variable is a global variable set to `None`. It is part of the Alembic migration script metadata, which can be used to label branches in a migration script for organizational purposes.
- **Use**: This variable is used to define branch labels for the Alembic migration script, although it is currently not set to any specific value.


---
### depends_on 
- **Type**: `NoneType`
- **Description**: The `depends_on` variable is a global variable set to `None`. It is part of the Alembic migration script metadata, which typically includes information about dependencies between migration scripts.
- **Use**: This variable is used to indicate that the current migration script does not depend on any other migration scripts.


---
### down_revision 
- **Type**: `str`
- **Description**: The `down_revision` variable is a string that holds the identifier of the previous database schema revision in an Alembic migration script. It is used to establish a linear sequence of migrations, allowing Alembic to determine the order in which migrations should be applied.
- **Use**: This variable is used by Alembic to track the migration history and ensure that migrations are applied in the correct order.


---
### revision 
- **Type**: `str`
- **Description**: The `revision` variable is a string that uniquely identifies the current database schema version in the context of Alembic migrations. It is used to track changes and manage the versioning of the database schema over time.
- **Use**: This variable is used by Alembic to apply or rollback migrations to the correct version of the database schema.


# Functions

---
### downgrade 
The `downgrade` function reverses database schema changes by dropping specific tables, columns, and indexes.
- **Inputs**:
    - None
- **Control Flow**:
    - The function begins by dropping an index on the 'derived_contents' table using the `op.drop_index` method.
    - It then removes the 'version_id' column from the 'derived_contents' table with the `op.drop_column` method.
    - Next, it drops the 'inspectorrun' table using the `op.drop_table` method.
    - Finally, it drops the 'inspection_versions' table using the `op.drop_table` method.
- **Output**:
    - The function does not return any value; it performs schema changes directly on the database.


---
### upgrade 
The `upgrade` function creates new database tables and modifies existing ones to add versioning capabilities using Alembic.
- **Inputs**:
    - None
- **Control Flow**:
    - The function begins by creating a new table named `inspection_versions` with columns for `id`, `version`, `display_name`, `created_at`, `updated_at`, and `previous_version_id`, along with a foreign key constraint on `previous_version_id` and a primary key constraint on `id`.
    - Next, it creates another table named `inspectorrun` with columns for `id`, `inspection_version_id`, `created_at`, and `updated_at`, including a foreign key constraint on `inspection_version_id` and a primary key constraint on `id`.
    - The function then adds a new column `version_id` to the existing `derived_contents` table.
    - An index is created on the `version_id` column of the `derived_contents` table to improve query performance.
    - Finally, a foreign key constraint is added to the `derived_contents` table linking `version_id` to the `id` column of the `inspection_versions` table.
- **Output**:
    - The function does not return any value; it performs database schema modifications.


