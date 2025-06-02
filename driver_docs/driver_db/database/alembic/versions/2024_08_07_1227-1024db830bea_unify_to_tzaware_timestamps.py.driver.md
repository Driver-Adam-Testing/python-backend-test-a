# Purpose
This Python file is an Alembic migration script designed to update the schema of a PostgreSQL database by ensuring that timestamp columns are timezone-aware. The script specifically targets tables with `created_at` and `updated_at` columns, converting these columns from non-timezone-aware `TIMESTAMP` types to timezone-aware `DateTime` types. The `upgrade` function is the core of this script, where it first updates any null values in the `created_at` and `updated_at` columns with the current UTC time, ensuring data consistency. It then alters the column types to be timezone-aware across several tables, such as `codebases`, `contentmetadata`, `derived_content_types`, and others, setting default values where necessary.

The script also includes a `downgrade` function, which reverses the changes made by the `upgrade` function, converting the columns back to their original non-timezone-aware types and adjusting their nullability and default values. This migration script is part of a broader database schema management process, providing a structured way to apply and revert changes to the database schema. The use of Alembic's `op` module and SQLAlchemy's data types and operations indicates that this script is intended to be executed within an Alembic migration environment, ensuring that database schema changes are applied consistently and can be tracked over time.
# Imports and Dependencies

---
- `datetime`
- `sqlalchemy`
- `alembic`
- `sqlalchemy.dialects.postgresql`


# Global Variables

---
### branch_labels 
- **Type**: `NoneType`
- **Description**: The `branch_labels` variable is a global variable set to `None`. It is part of the Alembic migration script metadata, which can be used to label branches in a migration history.
- **Use**: This variable is used to define branch labels for the migration script, but in this case, it is not utilized as it is set to `None`.


---
### depends_on 
- **Type**: `NoneType`
- **Description**: The `depends_on` variable is a global variable set to `None`. It is part of the Alembic migration script metadata, which typically indicates dependencies on other migrations.
- **Use**: This variable is used to specify if the current migration depends on any other migrations, but in this case, it indicates no dependencies by being set to `None`.


---
### down_revision 
- **Type**: `str`
- **Description**: The `down_revision` variable is a string that holds the identifier of the previous database schema revision in an Alembic migration script. It is used to establish a linear sequence of migrations, allowing Alembic to determine the order in which migrations should be applied.
- **Use**: This variable is used by Alembic to track and apply database schema changes in the correct order.


---
### revision 
- **Type**: `str`
- **Description**: The `revision` variable is a string that uniquely identifies the current database migration script. It is used by Alembic, a database migration tool for SQLAlchemy, to track and apply changes to the database schema.
- **Use**: This variable is used by Alembic to identify and manage the specific migration script within the version control system for database schema changes.


# Functions

---
### downgrade 
The `downgrade` function reverts database schema changes by altering several timestamp columns to be non-timezone aware and nullable.
- **Inputs**:
    - None
- **Control Flow**:
    - The function begins by altering the 'updated_at' column in the 'workspaces' table to change its type from timezone-aware DateTime to non-timezone-aware TIMESTAMP and make it nullable.
    - It then alters the 'created_at' column in the 'workspaces' table similarly, also removing the server default of 'now()'.
    - The function proceeds to alter the 'created_at' column in the 'runtimelogagentmessage' table to make it nullable.
    - It continues by altering both 'updated_at' and 'created_at' columns in the 'runtimelogagentinstance' table to make them nullable.
    - The 'created_at' column in the 'runtimelogagenterror' table is altered to be nullable.
    - The function alters the 'updated_at' and 'created_at' columns in the 'derived_contents' table, changing their types and making them nullable, also removing the server default for 'created_at'.
    - It alters the 'updated_at' and 'created_at' columns in the 'derived_content_types' table similarly.
    - The 'updated_at' and 'created_at' columns in the 'contentmetadata' table are altered to be nullable.
    - Finally, the 'updated_at' and 'created_at' columns in the 'codebases' table are altered to change their types and make them nullable, also removing the server default for 'created_at'.
- **Output**:
    - The function does not return any value; it performs schema alterations on the database.


---
### execute_update 
The `execute_update` function executes a given SQL statement using a database connection and prints the number of rows affected.
- **Inputs**:
    - `statement`: A string representing the SQL statement to be executed.
    - `conn`: A database connection object used to execute the SQL statement.
- **Control Flow**:
    - The function receives a SQL statement and a database connection as arguments.
    - It executes the SQL statement using the provided connection by converting the statement into a SQLAlchemy text object.
    - The result of the execution is stored in the `result` variable.
    - The number of rows affected by the execution is retrieved from `result.rowcount`.
    - A message is printed to the console indicating the executed statement and the number of rows affected.
- **Output**:
    - The function does not return any value; it performs an action and prints output to the console.


---
### update_created_at_only 
The `update_created_at_only` function updates the `created_at` column of a specified table to a given timestamp where the column is currently NULL.
- **Inputs**:
    - `table`: The name of the database table to update.
    - `created_at_col`: The name of the column in the table that stores the creation timestamp.
    - `timestamp`: A `datetime` object representing the timestamp to set for NULL entries in the `created_at` column.
    - `conn`: A database connection object used to execute the update statement.
- **Control Flow**:
    - The function constructs an SQL UPDATE statement to set the `created_at_col` to the provided `timestamp` for all rows where `created_at_col` is NULL.
    - The constructed SQL statement is passed to the `execute_update` function along with the database connection `conn` to perform the update operation.
- **Output**:
    - The function does not return any value; it performs an in-place update on the database table.


---
### update_timestamps 
The `update_timestamps` function updates the `created_at` and `updated_at` columns in a database table to ensure they are not null, using a provided timestamp if necessary.
- **Inputs**:
    - `table`: The name of the database table to update.
    - `created_at_col`: The name of the column representing the creation timestamp.
    - `updated_at_col`: The name of the column representing the update timestamp.
    - `timestamp`: A `datetime` object representing the timestamp to use for null values.
    - `conn`: A database connection object used to execute SQL statements.
- **Control Flow**:
    - Check if `created_at_col` is different from `updated_at_col`.
    - If they are different, execute an SQL update to set `updated_at_col` to the value of `created_at_col` where `created_at_col` is not null and `updated_at_col` is null.
    - Execute an SQL update to set both `created_at_col` and `updated_at_col` to the provided `timestamp` where either column is null, using `COALESCE` to handle null values.
- **Output**:
    - The function does not return any value; it performs updates directly on the database table.


---
### upgrade 
The `upgrade` function updates timestamp columns in various database tables to be timezone-aware and sets default values for missing timestamps.
- **Inputs**:
    - None
- **Control Flow**:
    - Retrieve the current datetime in UTC and establish a database connection.
    - Define two lists of tables: one with both 'created_at' and 'updated_at' columns, and another with only 'created_at' columns.
    - Iterate over the tables with both 'created_at' and 'updated_at' columns, calling `update_timestamps` to update missing timestamps.
    - Iterate over the tables with only 'created_at' columns, calling `update_created_at_only` to update missing timestamps.
    - Alter the columns in each table to ensure they are timezone-aware and have default values set to the current timestamp.
- **Output**:
    - The function does not return any value; it performs database schema and data updates.


