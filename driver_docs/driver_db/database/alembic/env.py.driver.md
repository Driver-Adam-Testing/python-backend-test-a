# Purpose
This Python script is designed to manage database schema migrations using Alembic, a lightweight database migration tool for SQLAlchemy. The script is structured to handle both "offline" and "online" migration modes, which are essential for applying database schema changes in different environments. The script imports necessary modules and configurations, including database settings and model definitions from two different versions (`models_v1` and `models_v2`). It defines a function `get_url` to retrieve the database connection URL from the settings, and an `include_object` function to filter out specific database objects, such as manually managed indexes, from the migration process.

The script's primary functionality is encapsulated in two functions: `run_migrations_offline` and `run_migrations_online`. The `run_migrations_offline` function configures the migration context for offline mode, where migrations are generated as SQL scripts without requiring a live database connection. Conversely, `run_migrations_online` establishes a connection to the database and executes migrations directly. It includes a mechanism to lock the `alembic_version` table to prevent concurrency issues during migrations. The script checks the mode of operation using `context.is_offline_mode()` and executes the appropriate migration function. This script is a critical component for maintaining database schema consistency across different environments and versions of the application.
# Imports and Dependencies

---
- `datetime`
- `logging.config`
- `alembic`
- `database.config`
- `database.models_v1`
- `database.models_v2`
- `sqlalchemy`
- `sqlalchemy.engine`
- `sqlmodel`


# Global Variables

---
### config 
- **Type**: ``alembic.config.Config``
- **Description**: The `config` variable is an instance of Alembic's `Config` class, which is used to manage configuration settings for database migrations. It is initialized by accessing the `config` attribute from the Alembic `context` module, which provides the configuration context for the migration environment.
- **Use**: This variable is used to retrieve and manage configuration settings necessary for running database migrations, such as the configuration file name and database connection details.


---
### target_metadata 
- **Type**: `SQLModel.metadata`
- **Description**: `target_metadata` is a global variable that holds the metadata object associated with the SQLModel class. This metadata object contains information about the database schema, such as tables, columns, and relationships, which is used by SQLAlchemy for database operations.
- **Use**: This variable is used to provide schema information to Alembic during database migrations.


# Functions

---
### get_url 
The `get_url` function retrieves the SQLAlchemy database URI from the application settings.
- **Inputs**:
    - None
- **Control Flow**:
    - The function accesses the `settings` module to retrieve the `SQLALCHEMY_DATABASE_URI` attribute.
    - It converts the URI to a string using the `str()` function.
    - The function returns the string representation of the database URI.
- **Output**:
    - The function returns a string that represents the SQLAlchemy database URI.


---
### include_object 
The `include_object` function determines whether a database object should be included in Alembic's migration process based on its type and name.
- **Inputs**:
    - `object_`: The database object being considered for inclusion.
    - `name`: The name of the database object.
    - `type_`: The type of the database object, such as 'index' or 'column'.
    - `reflected`: A parameter indicating if the object is reflected from the database schema.
    - `compare_to`: A parameter for comparison purposes, typically used in migration scripts.
- **Control Flow**:
    - Check if the object type is 'index' and its name matches specific manually managed index names; if so, return False.
    - Check if the object type is 'column' and its name is '__ts_vector__'; if so, return False.
    - If none of the above conditions are met, return True to include the object in the migration process.
- **Output**:
    - A boolean value indicating whether the object should be included (True) or excluded (False) from the migration process.


---
### run_migrations_offline 
The function `run_migrations_offline` configures and executes database migrations in an offline mode using Alembic.
- **Inputs**:
    - None
- **Control Flow**:
    - Retrieve the database URL using the `get_url` function.
    - Configure the Alembic context with the retrieved URL, target metadata, and other options such as literal binds, type comparison, and named parameter style.
    - Specify the `include_object` function to determine which database objects should be included in the migration process.
    - Begin a transaction using `context.begin_transaction()`.
    - Execute the migrations using `context.run_migrations()`.
- **Output**:
    - The function does not return any value; it performs database migrations in offline mode as a side effect.


---
### run_migrations_online 
The `run_migrations_online` function executes database migrations in an online mode using SQLAlchemy and Alembic.
- **Inputs**:
    - None
- **Control Flow**:
    - Retrieve the configuration section for the database connection from Alembic's config object.
    - Set the SQLAlchemy URL in the configuration using the `get_url` function.
    - Create a connectable engine using `engine_from_config` with the specified configuration and a `NullPool`.
    - Establish a connection to the database using the connectable engine.
    - Configure the Alembic context with the connection, target metadata, type comparison, and object inclusion rules.
    - Begin a transaction within the context.
    - Check if the `alembic_version` table exists in the database using the `table_exists` function.
    - If the `alembic_version` table exists, lock it in exclusive mode to prevent concurrent migrations.
    - Print the current datetime and run the migrations using `context.run_migrations()`.
    - Print the completion datetime after migrations are executed.
- **Output**:
    - The function does not return any value; it performs database migrations as a side effect.


---
### table_exists 
The `table_exists` function checks if a specified table exists in a given database connection.
- **Inputs**:
    - `connection`: A SQLAlchemy Connection object representing the database connection to inspect.
    - `table_name`: A string representing the name of the table to check for existence.
- **Control Flow**:
    - Create an inspector object using the provided database connection.
    - Retrieve the list of table names from the inspector.
    - Check if the specified table name is in the list of table names and return the result as a boolean.
- **Output**:
    - A boolean value indicating whether the specified table exists in the database.


