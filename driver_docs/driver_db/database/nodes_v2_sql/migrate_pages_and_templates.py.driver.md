# Purpose
The provided SQL script is designed to migrate data from a table named `derived_contents` to a new schema involving three tables: `v2_primary_asset`, `v2_version`, and `v2_node`. This script is structured as a series of Common Table Expressions (CTEs) that facilitate the transformation and insertion of data into these new tables. The primary focus is on handling content items identified as 'application_note' or 'template', ensuring that each content item is uniquely identified and appropriately categorized in the new schema. The script uses SQL constructs like `ROW_NUMBER` to handle duplicate content names within the same organization, appending a suffix to differentiate them.

The script performs several key operations: it first selects and processes relevant data from `derived_contents` and `workspaces` to create a temporary dataset (`pages`). It then inserts this data into `v2_primary_asset`, `v2_version`, and `v2_node`, reusing the original IDs from `derived_contents` to maintain consistency across the new tables. Each insertion is followed by a `RETURNING` clause to confirm the operation's success. Finally, the script updates the `derived_contents` table to link each entry to its corresponding node in the new schema. This migration script is a crucial component for transitioning data to a more structured and scalable format, likely as part of a broader database schema evolution or application upgrade.
# Global Variables

---
### MIGRATE_PAGES 
- **Type**: `str`
- **Description**: The `MIGRATE_PAGES` variable is a multi-line string containing a SQL script. This script is designed to migrate data from a table named `derived_contents` to several other tables (`v2_primary_asset`, `v2_version`, `v2_node`) by inserting and updating records based on certain conditions and transformations. The script uses common table expressions (CTEs) to structure the migration process, ensuring that data is correctly partitioned, ordered, and inserted into the new schema.
- **Use**: This variable is used to store the SQL script for migrating page data within a database, facilitating the transition to a new data model.


