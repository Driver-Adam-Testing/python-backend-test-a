# Purpose
This source code file is an Alembic migration script designed to modify the database schema by altering foreign key constraints. It provides narrow functionality specific to database schema management, particularly focusing on cascading deletions for the `derived_contents` and `document_sources` tables. The `upgrade` function removes existing foreign key constraints and creates new ones with the `ondelete="CASCADE"` option, ensuring that deletions in the `v2_node` table propagate to these tables. Conversely, the `downgrade` function reverses these changes, restoring the original foreign key constraints without the cascade option. This script is part of a version-controlled database migration process, facilitating schema evolution in a controlled manner.
# Imports and Dependencies

---
- `alembic`


# Global Variables

---
### branch_labels 
- **Type**: `NoneType`
- **Description**: The `branch_labels` variable is a global variable set to `None`. It is part of the Alembic migration script metadata, which is used to define labels for branches in a database migration context.
- **Use**: This variable is used to specify branch labels for the migration, but in this case, it is not utilized as it is set to `None`.


---
### depends_on 
- **Type**: `NoneType`
- **Description**: The `depends_on` variable is a global variable set to `None`. It is part of the Alembic migration script metadata, which typically includes information about dependencies between migration scripts.
- **Use**: This variable is used to indicate that the current migration script does not depend on any other migration script.


---
### down_revision 
- **Type**: `str`
- **Description**: The `down_revision` variable is a string that holds the identifier of the previous database schema revision in an Alembic migration script. It is used to establish a linear sequence of migrations, allowing Alembic to determine the order in which migrations should be applied.
- **Use**: This variable is used by Alembic to track the migration history and ensure that migrations are applied in the correct order.


---
### revision 
- **Type**: `str`
- **Description**: The `revision` variable is a string that uniquely identifies the current database schema migration revision in Alembic. It is used to track the specific version of the database schema that this migration script represents.
- **Use**: This variable is used by Alembic to manage and apply database schema migrations in a version-controlled manner.


# Functions

---
### downgrade 
The `downgrade` function reverts database schema changes by dropping and recreating foreign key constraints without cascade delete options.
- **Inputs**:
    - None
- **Control Flow**:
    - Drop two unnamed foreign key constraints from the 'document_sources' table.
    - Create a foreign key constraint 'document_sources_source_node_id_fkey' on the 'document_sources' table referencing 'v2_node'.
    - Create a foreign key constraint 'document_sources_page_node_id_fkey' on the 'document_sources' table referencing 'v2_node'.
    - Drop an unnamed foreign key constraint from the 'derived_contents' table.
    - Create a foreign key constraint 'derived_contents_node_id_fkey' on the 'derived_contents' table referencing 'v2_node'.
- **Output**:
    - The function does not return any value; it performs schema modifications on the database.


---
### upgrade 
The `upgrade` function modifies foreign key constraints in the database schema to enable cascading deletions for specific tables.
- **Inputs**:
    - None
- **Control Flow**:
    - Drop the existing foreign key constraint 'derived_contents_node_id_fkey' from the 'derived_contents' table.
    - Create a new foreign key constraint on 'derived_contents' table linking 'node_id' to 'id' in 'v2_node' table with 'CASCADE' delete rule.
    - Drop the existing foreign key constraints 'document_sources_page_node_id_fkey' and 'document_sources_source_node_id_fkey' from the 'document_sources' table.
    - Create a new foreign key constraint on 'document_sources' table linking 'page_node_id' to 'id' in 'v2_node' table with 'CASCADE' delete rule.
    - Create another foreign key constraint on 'document_sources' table linking 'source_node_id' to 'id' in 'v2_node' table with 'CASCADE' delete rule.
- **Output**:
    - The function does not return any value; it performs schema modifications directly on the database.


