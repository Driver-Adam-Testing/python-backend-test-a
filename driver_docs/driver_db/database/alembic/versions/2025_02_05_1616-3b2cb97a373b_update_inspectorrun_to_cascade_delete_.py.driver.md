# Purpose
This source code file is an Alembic migration script for a SQLAlchemy-managed database, providing narrow functionality focused on modifying the schema of a specific table. The script updates the `InspectorRun` table to enforce a cascade delete behavior on the `version_id` foreign key, ensuring that deletions in the referenced `v2_version` table propagate to `InspectorRun`. Additionally, it removes the `inspection_version_id` column from the `InspectorRun` table. The `upgrade` function implements these changes, while the `downgrade` function reverses them, restoring the original schema state. This script is part of a version-controlled database migration process, facilitating schema evolution in a controlled manner.
# Imports and Dependencies

---
- `sqlalchemy`
- `alembic`


# Global Variables

---
### branch_labels 
- **Type**: `NoneType`
- **Description**: The `branch_labels` variable is a global variable set to `None`. It is part of the Alembic migration script metadata, which is used to define characteristics of the migration, such as branching labels for version control.
- **Use**: This variable is used to specify branch labels for the migration, but in this case, it is not utilized as it is set to `None`.


---
### depends_on 
- **Type**: `NoneType`
- **Description**: The `depends_on` variable is a global variable set to `None`. It is part of the Alembic migration script metadata, which typically indicates dependencies on other migrations.
- **Use**: This variable is used to specify that the current migration does not depend on any other migrations.


---
### down_revision 
- **Type**: `str`
- **Description**: The `down_revision` variable is a string that holds the identifier of the previous database schema revision in an Alembic migration script. It is used to establish a linear sequence of migrations, allowing Alembic to determine the order in which migrations should be applied.
- **Use**: This variable is used by Alembic to track and apply database schema changes in the correct order.


---
### revision 
- **Type**: `string`
- **Description**: The `revision` variable is a string that uniquely identifies the current database migration script in the Alembic migration framework. It is used to track the specific changes made to the database schema in this migration.
- **Use**: This variable is used by Alembic to manage and apply database schema migrations in a controlled manner.


# Functions

---
### downgrade 
The `downgrade` function reverts database schema changes by adding a column, modifying foreign key constraints, and altering column nullability.
- **Inputs**:
    - None
- **Control Flow**:
    - Adds a new column `inspection_version_id` to the `inspectorrun` table with type `UUID` and allows null values.
    - Drops an existing foreign key constraint from the `inspectorrun` table.
    - Creates a new foreign key constraint `inspectorrun_version_id_fkey` on the `inspectorrun` table referencing the `v2_version` table, with `ondelete` set to `SET NULL`.
    - Alters the `version_id` column in the `inspectorrun` table to allow null values.
- **Output**:
    - The function does not return any value; it performs schema modifications on the database.


---
### upgrade 
The `upgrade` function modifies the database schema for the `inspectorrun` table by enforcing non-null constraints, updating foreign key relationships, and removing a column.
- **Inputs**:
    - None
- **Control Flow**:
    - Execute a SQL command to delete rows from the `inspectorrun` table where `version_id` is NULL.
    - Alter the `version_id` column in the `inspectorrun` table to make it non-nullable.
    - Drop the existing foreign key constraint on the `version_id` column in the `inspectorrun` table.
    - Create a new foreign key constraint on the `version_id` column in the `inspectorrun` table, referencing the `id` column in the `v2_version` table with a CASCADE delete rule.
    - Drop the `inspection_version_id` column from the `inspectorrun` table.
- **Output**:
    - The function does not return any value; it performs schema modifications on the database.


