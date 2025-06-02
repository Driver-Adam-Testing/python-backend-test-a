# Purpose
This code is a string variable named `MIGRATE_TOP_LEVEL` that contains a SQL script designed to update records in a database table named `derived_contents`. The script performs a series of `UPDATE` operations to change the `content_kind` of entries based on specific conditions, effectively migrating content descriptions to a new top-level categorization. Each `UPDATE` statement targets entries where the `source_content_id` matches the `id` of another entry with a `content_kind` of 'codebase', and updates the `content_kind` to a new top-level category such as 'TOP_LEVEL_TERSE_SENTENCE' or 'TOP_LEVEL_LONG_DESCRIPTION'. This code provides narrow functionality, specifically for database migration tasks related to content categorization, and is likely part of a larger data migration or transformation process.
# Global Variables

---
### MIGRATE_TOP_LEVEL 
- **Type**: `str`
- **Description**: The `MIGRATE_TOP_LEVEL` variable is a multi-line string containing a series of SQL commands. These commands are designed to update the `content_kind` field in the `derived_contents` table based on certain conditions, effectively migrating content types to a 'TOP_LEVEL' designation.
- **Use**: This variable is used to store SQL migration commands that update content types in a database.


