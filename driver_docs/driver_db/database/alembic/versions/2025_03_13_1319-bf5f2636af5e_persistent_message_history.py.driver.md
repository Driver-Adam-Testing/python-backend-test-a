# Purpose
This Python file is an Alembic migration script designed to modify a database schema by creating new tables and indexes related to a persistent message history system. The script defines three main tables: `v2_runtime_llm_session`, `v2_runtime_llm_message_history`, and `v2_runtime_llm_messages`. These tables are structured to store information about sessions, message histories, and individual messages, respectively, in a system that likely involves large language models (LLMs). The `v2_runtime_llm_session` table includes columns for session identifiers, user and organization IDs, and timestamps for creation and updates. The `v2_runtime_llm_message_history` table links to sessions and categorizes message histories by a pipeline kind, while the `v2_runtime_llm_messages` table stores individual messages with JSON content and a hash for identification.

The script uses SQLAlchemy and Alembic to define the schema changes, including the creation of foreign key constraints and indexes to optimize query performance. The `upgrade` function implements the schema changes, while the `downgrade` function reverses them, ensuring that the database can be rolled back to its previous state if necessary. This migration script is part of a broader database management process, facilitating the evolution of the database schema in a controlled and reversible manner. It is intended to be executed as part of a series of migrations, as indicated by the revision identifiers and dependencies.
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
- **Use**: This variable is used to specify branch labels for the migration, but in this case, it is not utilized as it is set to `None`.


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
- **Type**: `string`
- **Description**: The `revision` variable is a string that uniquely identifies the current version of the database schema in the context of Alembic migrations. It is used to track changes and manage the versioning of the database schema over time.
- **Use**: This variable is used by Alembic to identify the current migration script and ensure the correct application of database schema changes.


# Functions

---
### downgrade 
The `downgrade` function reverses database schema changes by dropping specific tables and indexes.
- **Inputs**:
    - None
- **Control Flow**:
    - The function begins by dropping the index 'ix_v2_runtime_llm_messages_message_history_id' from the 'v2_runtime_llm_messages' table.
    - It then drops the 'v2_runtime_llm_messages' table entirely.
    - Next, it drops the indexes 'ix_v2_runtime_llm_message_history_pipeline_kind' and 'ix_v2_runtime_llm_message_history_llm_session_id' from the 'v2_runtime_llm_message_history' table.
    - The 'v2_runtime_llm_message_history' table is then dropped.
    - The function proceeds to drop the indexes 'ix_v2_runtime_llm_session_user_id' and 'ix_v2_runtime_llm_session_organization_id' from the 'v2_runtime_llm_session' table.
    - Finally, the 'v2_runtime_llm_session' table is dropped.
- **Output**:
    - The function does not return any value; it performs database schema modifications.


---
### upgrade 
The `upgrade` function creates three new database tables and their associated indexes to support runtime LLM sessions, message history, and messages.
- **Inputs**:
    - None
- **Control Flow**:
    - The function begins by creating a table named `v2_runtime_llm_session` with columns for session ID, user ID, organization ID, source node IDs, page node ID, and timestamps for creation and update.
    - Indexes are created for the `organization_id` and `user_id` columns of the `v2_runtime_llm_session` table to optimize queries.
    - A second table, `v2_runtime_llm_message_history`, is created with columns for message history ID, LLM session ID, and pipeline kind, with a foreign key constraint linking `llm_session_id` to the `v2_runtime_llm_session` table.
    - Indexes are created for the `llm_session_id` and `pipeline_kind` columns of the `v2_runtime_llm_message_history` table.
    - A third table, `v2_runtime_llm_messages`, is created with columns for message ID, message history ID, message hash, message JSON, and timestamps, with a foreign key constraint linking `message_history_id` to the `v2_runtime_llm_message_history` table.
    - An index is created for the `message_history_id` column of the `v2_runtime_llm_messages` table.
- **Output**:
    - The function does not return any value; it performs database schema modifications.


