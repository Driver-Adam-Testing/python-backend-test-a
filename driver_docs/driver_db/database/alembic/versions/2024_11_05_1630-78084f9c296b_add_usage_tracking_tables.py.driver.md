# Purpose
This Python file is an Alembic migration script designed to modify a database schema by adding tables for tracking usage data. Specifically, it introduces two new tables: `usage_sessions` and `usage_events`. The `usage_sessions` table is intended to record sessions with fields such as `id`, `status`, `organization_id`, `user_id`, `metadata`, and timestamps for creation and updates. The `status` field uses an enumerated type to indicate the session's state, such as "RUNNING", "COMPLETED", or "FAILED". The `usage_events` table is designed to log individual events within a session, capturing details like `event_type`, `session_id`, `organization_id`, `user_id`, `event_source`, data transfer metrics (`bytes_in`, `bytes_out`, `tokens_in`, `tokens_out`), and a timestamp. The `session_id` field in `usage_events` is a foreign key referencing the `usage_sessions` table, ensuring referential integrity and allowing for cascading deletes.

The script includes both `upgrade` and `downgrade` functions, which are standard in Alembic migrations. The `upgrade` function creates the tables and indexes, while the `downgrade` function reverses these changes by dropping the tables and indexes, as well as the enumerated type used for session status. This script is a part of a broader database migration process, facilitating the evolution of the database schema over time. It is not intended to be a standalone script but rather a component of a larger system that uses Alembic for managing database migrations.
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
- **Description**: The `branch_labels` variable is a global variable set to `None`. It is part of the Alembic migration script metadata, which is used to define branch labels for the migration script.
- **Use**: This variable is used to specify branch labels for the Alembic migration, but in this case, it is not being utilized as it is set to `None`.


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
- **Type**: ``str``
- **Description**: The `revision` variable is a string that serves as a unique identifier for the current database migration script. It is used by Alembic, a database migration tool for SQLAlchemy, to track and apply changes to the database schema.
- **Use**: This variable is used by Alembic to identify the specific migration script when applying or rolling back database schema changes.


# Functions

---
### downgrade 
The `downgrade` function reverses database schema changes by dropping tables, indexes, and a type related to usage tracking.
- **Inputs**:
    - None
- **Control Flow**:
    - The function begins by dropping the index 'ix_usage_events_session_id' from the 'usage_events' table.
    - It then drops the 'usage_events' table entirely.
    - Next, it drops the index 'ix_usage_sessions_status' from the 'usage_sessions' table.
    - It proceeds to drop the 'usage_sessions' table.
    - Finally, it executes a raw SQL command to drop the type 'usagesessionstatus' if it exists.
- **Output**:
    - The function does not return any value; it performs database schema modifications.


---
### upgrade 
The `upgrade` function creates two new database tables, `usage_sessions` and `usage_events`, along with their respective indexes, to track usage data.
- **Inputs**:
    - None
- **Control Flow**:
    - The function begins by creating a new table named `usage_sessions` with columns for `id`, `status`, `organization_id`, `user_id`, `metadata`, `created_at`, and `updated_at`, where `id` is the primary key.
    - An index is created on the `status` column of the `usage_sessions` table to optimize queries filtering by status.
    - Next, the function creates another table named `usage_events` with columns for `id`, `event_type`, `session_id`, `organization_id`, `user_id`, `event_source`, `bytes_in`, `bytes_out`, `tokens_in`, `tokens_out`, `timestamp`, and `metadata`, where `id` is the primary key.
    - A foreign key constraint is added to the `usage_events` table linking `session_id` to the `id` column of the `usage_sessions` table, with a cascade delete option.
    - An index is created on the `session_id` column of the `usage_events` table to optimize queries filtering by session ID.
- **Output**:
    - The function does not return any value; it performs database schema modifications as a side effect.


