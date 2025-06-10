# Purpose
This Python file is an Alembic migration script designed to modify the database schema by introducing new ENUM types and updating existing data to align with these types. The script defines two new ENUM types, `primaryassetkind` and `versionstatus`, which are used to categorize data in the `v2_primary_asset` and `v2_version` tables, respectively. The `upgrade` function executes SQL commands to create these ENUM types and alters the columns in the specified tables to use these new types. Additionally, it updates the `status` field in the `v2_version` table to replace hyphens with underscores, addressing a previous migration bug.

The `downgrade` function provides the reverse operations to revert the schema changes, converting the ENUM columns back to VARCHAR and dropping the ENUM types. This script is a part of a series of migrations, as indicated by the `revision` and `down_revision` identifiers, which help track the sequence of changes in the database schema. The script is intended to be executed as part of a larger migration process, ensuring that the database structure evolves in a controlled and consistent manner.
# Imports and Dependencies

---
- `alembic`


# Global Variables

---
### branch_labels 
- **Type**: `NoneType`
- **Description**: The variable `branch_labels` is set to `None`, indicating that there are no specific branch labels associated with this Alembic migration script. In Alembic, branch labels are used to identify branches in the migration history, but in this case, it is not utilized.
- **Use**: This variable is used to define branch labels for the migration script, but it is set to `None`, indicating no branch labels are applied.


---
### depends_on 
- **Type**: `NoneType`
- **Description**: The `depends_on` variable is a global variable set to `None`. It is part of the Alembic migration script metadata, which typically includes information about dependencies between migration scripts.
- **Use**: This variable is used to indicate that the current migration script does not depend on any other migration scripts.


---
### down_revision 
- **Type**: `str`
- **Description**: The `down_revision` variable is a string that holds the identifier of the previous database schema revision in a sequence of migrations. It is used by Alembic, a database migration tool for SQLAlchemy, to determine the order of migrations and ensure that they are applied in the correct sequence.
- **Use**: This variable is used by Alembic to track the dependency of the current migration on a previous migration, ensuring proper migration order.


---
### revision 
- **Type**: `str`
- **Description**: The `revision` variable is a string that represents the unique identifier for the current database migration script. It is used by Alembic, a database migration tool for SQLAlchemy, to track and apply changes to the database schema.
- **Use**: This variable is used to identify the specific migration script within the Alembic migration framework.


# Functions

---
### downgrade 
The `downgrade` function reverts database schema changes by altering column types from enums back to VARCHAR and dropping the enum types.
- **Inputs**:
    - None
- **Control Flow**:
    - Execute SQL command to alter the 'status' column in the 'v2_version' table from an enum type to VARCHAR using a cast to TEXT.
    - Execute SQL command to alter the 'kind' column in the 'v2_primary_asset' table from an enum type to VARCHAR using a cast to TEXT.
    - Execute SQL command to drop the 'versionstatus' enum type from the database.
    - Execute SQL command to drop the 'primaryassetkind' enum type from the database.
- **Output**:
    - The function does not return any value; it performs database schema modifications.


---
### upgrade 
The `upgrade` function performs a database schema migration by creating new ENUM types and updating existing table columns to use these types.
- **Inputs**:
    - None
- **Control Flow**:
    - Execute SQL command to create ENUM type `primaryassetkind` with values 'CODEBASE', 'FILE', 'PAGE', 'PAGE_TEMPLATE'.
    - Execute SQL command to create ENUM type `versionstatus` with values 'GENERATING', 'GENERATION_COMPLETE', 'GENERATION_ERROR'.
    - Execute SQL command to update the `status` column in `v2_version` table, replacing '-' with '_'.
    - Execute SQL command to alter the `kind` column in `v2_primary_asset` table to use the `primaryassetkind` ENUM type, casting existing values.
    - Execute SQL command to alter the `status` column in `v2_version` table to use the `versionstatus` ENUM type, casting existing values.
- **Output**:
    - The function does not return any value; it performs database operations to modify the schema.


