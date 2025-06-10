# Purpose
The provided SQL script is designed to migrate and transform data related to PDF documents from an existing database schema to a new schema. The script is structured as a series of Common Table Expressions (CTEs) that systematically process and insert data into new tables while maintaining relationships between the old and new data structures. The primary focus is on handling records where the `content_kind` is 'supplemental-document', which are extracted from the `derived_contents` table. The script ensures that each document is assigned a unique version number and a row key for identification and bridging purposes.

The script performs several key operations: it first gathers relevant PDF records, then selects distinct records to be used as primary assets in the new schema. It inserts these assets into the `v2_primary_asset` table and establishes a bridge to link these assets back to their original records. Subsequently, it inserts all versions of the documents into the `v2_version` table, followed by creating corresponding nodes in the `v2_node` table. Each step involves careful bridging to maintain data integrity and traceability. Finally, the script updates the `derived_contents` table to reflect the new node associations, completing the migration process. This script is a comprehensive data migration tool that ensures a seamless transition of document records to a new database structure while preserving historical data and relationships.
# Global Variables

---
### MIGRATE_PDFS 
- **Type**: `str`
- **Description**: The `MIGRATE_PDFS` variable is a multi-line string containing a SQL script. This script is designed to migrate PDF-related data from a source table to a new schema, involving several steps such as selecting, inserting, and updating data across multiple tables. The script uses Common Table Expressions (CTEs) to organize the migration process into distinct phases, ensuring data integrity and proper versioning.
- **Use**: This variable is used to store the SQL script that performs the migration of PDF data, which can be executed within a database context to update and restructure the data as specified.


