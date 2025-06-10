# Purpose
This Python file is an Alembic migration script designed to modify a database schema by adding new tables related to Git provider applications. The script defines two main tables: `git_provider_apps` and `git_provider_app_installations`. The `git_provider_apps` table stores information about different Git provider applications, including their type, owner organization, and configuration details such as client ID and redirect URI. It also includes timestamps for creation and updates. The `git_provider_app_installations` table records installations of these applications, linking them to specific organizations and users, and includes a foreign key constraint to ensure referential integrity with the `git_provider_apps` table. The script also creates several indexes to optimize query performance on key columns.

The script is structured to support both upgrading and downgrading the database schema. The `upgrade` function contains commands to create the tables and indexes, while the `downgrade` function includes commands to drop them, effectively reversing the changes made by the upgrade. This migration script is part of a broader database versioning system, allowing for controlled and reversible changes to the database schema. The use of Alembic, a database migration tool for SQLAlchemy, indicates that this script is intended to be part of a larger application that manages database schema changes in a systematic and version-controlled manner.
# Imports and Dependencies

---
- `sqlalchemy`
- `sqlmodel.sql.sqltypes`
- `alembic.op`


# Global Variables

---
### branch_labels 
- **Type**: `NoneType`
- **Description**: The `branch_labels` variable is a global variable set to `None`. It is part of the Alembic migration script metadata, which typically includes revision identifiers and dependencies.
- **Use**: This variable is used to define branch labels for the migration script, but in this case, it is not utilized as it is set to `None`.


---
### depends_on 
- **Type**: `NoneType`
- **Description**: The `depends_on` variable is a global variable set to `None`. It is part of the Alembic migration script metadata, which is used to define dependencies between different database schema revisions.
- **Use**: This variable is used by Alembic to determine if the current migration depends on any other migrations being applied first.


---
### down_revision 
- **Type**: `str`
- **Description**: The `down_revision` variable is a string that represents the identifier of the previous database schema revision in an Alembic migration script. It is used to establish a linear sequence of migrations, allowing Alembic to determine the order in which migrations should be applied or rolled back.
- **Use**: This variable is used by Alembic to track and manage the sequence of database schema changes.


---
### revision 
- **Type**: ``str``
- **Description**: The `revision` variable is a string that uniquely identifies the current database schema version in the context of Alembic migrations. It is used as a revision identifier to track changes made to the database schema over time.
- **Use**: This variable is used by Alembic to apply or rollback database migrations to the specific schema version identified by this revision ID.


# Functions

---
### downgrade 
The `downgrade` function reverses database schema changes by dropping specific tables, indexes, and a type related to git provider applications.
- **Inputs**:
    - None
- **Control Flow**:
    - The function begins by dropping the index 'ix_git_provider_app_installations_git_provider_app_id' from the 'git_provider_app_installations' table.
    - It then drops the 'git_provider_app_installations' table entirely.
    - Next, it drops three indexes from the 'git_provider_apps' table: 'ix_git_provider_apps_provider_kind', 'ix_git_provider_apps_owner_organization_id', and 'ix_git_provider_apps_client_id'.
    - The 'git_provider_apps' table is then dropped.
    - Finally, the function executes a raw SQL command to drop the type 'gitproviderkind' if it exists.
- **Output**:
    - The function does not return any value; it performs schema changes directly on the database.


---
### upgrade 
The `upgrade` function creates two new database tables, `git_provider_apps` and `git_provider_app_installations`, along with their respective indexes and constraints.
- **Inputs**:
    - None
- **Control Flow**:
    - The function begins by creating a new table named `git_provider_apps` with various columns including `id`, `provider_kind`, `shared_provider`, `owner_organization_id`, `name`, `base_url`, `client_id`, `redirect_uri`, `scopes`, `created_at`, and `updated_at`.
    - A primary key constraint is set on the `id` column of the `git_provider_apps` table.
    - Indexes are created on the `client_id`, `owner_organization_id`, and `provider_kind` columns of the `git_provider_apps` table, with the `client_id` index being unique.
    - The function then creates another table named `git_provider_app_installations` with columns `id`, `git_provider_app_id`, `organization_id`, `user_id`, `created_at`, and `updated_at`.
    - A foreign key constraint is established on the `git_provider_app_id` column of the `git_provider_app_installations` table, referencing the `id` column of the `git_provider_apps` table, with a cascade delete option.
    - A primary key constraint is set on the `id` column of the `git_provider_app_installations` table.
    - A unique constraint is applied to the combination of `git_provider_app_id`, `organization_id`, and `user_id` columns in the `git_provider_app_installations` table.
    - An index is created on the `git_provider_app_id` column of the `git_provider_app_installations` table.
- **Output**:
    - The function does not return any value as it is designed to perform database schema modifications.


