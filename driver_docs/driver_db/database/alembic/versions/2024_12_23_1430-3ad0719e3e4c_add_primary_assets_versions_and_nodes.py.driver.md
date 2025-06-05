# Purpose
This Python file is an Alembic migration script designed to modify a database schema by adding new tables and indexes related to primary assets, versions, and nodes. The script defines an upgrade function that creates several tables: `v2_primary_asset`, `v2_primary_asset_tag`, `v2_version`, and `v2_node`. Each table is equipped with specific columns and constraints, such as primary keys, foreign keys, and unique indexes, to ensure data integrity and efficient querying. For instance, the `v2_primary_asset` table includes columns for `id`, `display_name`, `repository_id`, `organization_id`, `kind`, `created_at`, and `updated_at`, with a unique index on the combination of `organization_id` and `display_name`. The `v2_version` table links to `v2_primary_asset` through a foreign key, and the `v2_node` table links to `v2_version`, establishing a relational structure that supports versioning and node management.

The script also includes a downgrade function to reverse the changes made by the upgrade function, ensuring that the database schema can be reverted to its previous state if necessary. This involves dropping the newly created tables and indexes. The use of Alembic, a database migration tool for SQLAlchemy, indicates that this script is part of a broader database version control system, allowing developers to manage and apply schema changes systematically. The script is not intended to be a standalone application but rather a component of a larger system that manages database schema evolution.
# Imports and Dependencies

---
- `sqlalchemy`
- `sqlmodel.sql.sqltypes`
- `alembic`
- `sqlalchemy.dialects.postgresql`


# Global Variables

---
### branch_labels 
- **Type**: `NoneType`
- **Description**: The `branch_labels` variable is a global variable set to `None`. It is part of the Alembic migration script metadata, which typically includes information about the migration such as revision identifiers and dependencies.
- **Use**: This variable is used to define branch labels for the migration, but in this case, it is not utilized as it is set to `None`.


---
### depends_on 
- **Type**: `NoneType`
- **Description**: The `depends_on` variable is a global variable set to `None`. It is part of the Alembic migration script metadata, which is used to specify dependencies between migration scripts.
- **Use**: This variable is used by Alembic to determine if the current migration script depends on any other migration scripts.


---
### down_revision 
- **Type**: `str`
- **Description**: The `down_revision` variable is a string that holds the identifier of the previous database schema revision in an Alembic migration script. It is used to establish a linear sequence of migrations, allowing Alembic to determine the order in which migrations should be applied.
- **Use**: This variable is used by Alembic to track and apply database schema changes in the correct order.


---
### revision 
- **Type**: ``str``
- **Description**: The `revision` variable is a string that serves as a unique identifier for a specific database schema migration in Alembic. It is used to track the version of the database schema that corresponds to this particular migration script.
- **Use**: This variable is used by Alembic to identify and apply the correct migration when upgrading or downgrading the database schema.


# Functions

---
### downgrade 
The `downgrade` function reverses database schema changes by dropping specific tables, columns, and indexes.
- **Inputs**:
    - None
- **Control Flow**:
    - The function begins by dropping the 'node_id' column from the 'derived_contents' table.
    - It then drops the 'ix_version_id_relative_path' index from the 'v2_node' table.
    - Next, it drops the 'ix_v2_node_relative_path' index from the 'v2_node' table.
    - The 'v2_node' table is then dropped entirely.
    - The function proceeds to drop the 'ix_v2_version_primary_asset_id_display_name' index from the 'v2_version' table.
    - It drops the 'v2_version' table.
    - The 'v2_primary_asset_tag' table is dropped next.
    - The 'ix_v2_primary_asset_organization_id_display_name' index is dropped from the 'v2_primary_asset' table.
    - Finally, the 'v2_primary_asset' table is dropped.
- **Output**:
    - The function does not return any value; it performs schema changes directly on the database.


---
### upgrade 
The `upgrade` function creates new database tables and indexes to support primary assets, versions, and nodes, and modifies existing tables to include new columns and foreign key constraints.
- **Inputs**:
    - None
- **Control Flow**:
    - The function begins by creating a new table `v2_primary_asset` with columns for ID, display name, repository ID, organization ID, kind, created and updated timestamps, and sets the ID as the primary key.
    - An index is created on the `v2_primary_asset` table for the combination of `organization_id` and `display_name`, ensuring uniqueness.
    - A new table `v2_primary_asset_tag` is created with columns for `tag_id` and `primary_asset_id`, both of which are foreign keys, and a composite primary key is set on these columns.
    - The function creates a `v2_version` table with columns for ID, primary asset ID, display name, created and updated timestamps, status, and previous version ID, with foreign key constraints linking to `v2_primary_asset` and itself, and sets the ID as the primary key.
    - An index is created on the `v2_version` table for the combination of `primary_asset_id` and `display_name`, ensuring uniqueness.
    - A `v2_node` table is created with columns for ID, kind, version ID, relative path, created and updated timestamps, and miscellaneous metadata, with a foreign key constraint linking to `v2_version`, and sets the ID as the primary key.
    - Indexes are created on the `v2_node` table for `relative_path` and the combination of `version_id` and `relative_path`, with the latter ensuring uniqueness.
    - A new column `node_id` is added to the `derived_contents` table, and an index is created on this column.
    - A foreign key constraint is added to the `derived_contents` table linking `node_id` to the `v2_node` table.
- **Output**:
    - The function does not return any value as it is designed to perform database schema modifications.


