# Purpose
The provided code is a SQL script designed to migrate and organize data related to codebases and their versions within a database. It performs a series of operations to prepare and insert primary assets and their versions, insert nodes representing directories and files, and update derived content records to link them with the newly created nodes. The script begins by creating temporary tables to resolve version IDs and mark primary assets, which are then inserted into the `v2_primary_asset` and `v2_version` tables. This establishes a structured relationship between codebases, their versions, and associated metadata.

The script continues by deduplicating nodes, which represent directories and files, and inserting them into the `v2_node` table. It ensures that each node is uniquely identified and linked to the correct version. Subsequent updates to the `derived_contents` table ensure that each content item is associated with the correct node, reflecting its hierarchical position within the codebase. The script concludes with optional selection of all nodes, ordered by creation date, to verify the migration's outcome. This SQL script is a comprehensive solution for organizing and migrating codebase data, ensuring consistency and integrity across related database tables.
# Global Variables

---
### MIGRATE_CODEBASE 
- **Type**: `str`
- **Description**: The `MIGRATE_CODEBASE` variable is a multi-line string containing a SQL script. This script is designed to migrate a codebase by preparing and inserting primary assets and versions, inserting nodes, and updating derived contents. It includes several SQL operations such as creating temporary tables, inserting data into tables, and updating existing records.
- **Use**: This variable is used to store the SQL script that performs the migration of a codebase within a database.


