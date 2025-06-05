# Purpose
This code is a SQL query stored as a multi-line string in a Python variable named `MIGRATE_TAGS`. It provides narrow functionality, specifically designed to migrate or associate tags with primary asset IDs in a database. The query first creates a temporary table, `tags_primary_asset_ids`, which selects distinct tag IDs and their corresponding primary asset IDs by joining several tables: `tags_contents`, `derived_contents`, `v2_node`, and `v2_version`. It then inserts these associations into the `v2_primary_asset_tag` table, ensuring that only non-null primary asset IDs are considered. The `RETURNING tag_id` clause indicates that the query will return the tag IDs that were successfully inserted, which can be useful for verification or logging purposes. This code is likely part of a larger data migration or transformation script used in a database management context.
# Global Variables

---
### MIGRATE_TAGS 
- **Type**: `str`
- **Description**: The `MIGRATE_TAGS` variable is a multi-line string containing a SQL query. This query is designed to migrate tag data by associating tags with primary asset IDs. It involves selecting distinct tag and primary asset ID pairs from a series of joined tables and inserting them into a new table, `v2_primary_asset_tag`, while returning the tag IDs.
- **Use**: This variable is used to store a SQL query for migrating tag data to a new table structure in a database.


