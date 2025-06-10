# Purpose
This Python code file is a configuration and setup script for a GraphQL API using the Strawberry library integrated with FastAPI. It defines a GraphQL schema with specified query and mutation operations, custom scalar type handling, and an extension for logging. The code also establishes a context class to manage session and user information, which is essential for handling authentication and database interactions. Two GraphQL routers are configured: one for general API access and another specifically for use with the Apollo Sandbox IDE, both utilizing the defined schema and context management. This setup provides a narrow but essential functionality for enabling GraphQL operations within a FastAPI application, focusing on authentication, session management, and logging.
# Imports and Dependencies

---
- `strawberry`
- `fastapi.Depends`
- `strawberry.fastapi.BaseContext`
- `strawberry.fastapi.GraphQLRouter`
- `strawberry.schema.config.StrawberryConfig`
- `app.api.auth.get_current_m2m`
- `app.api.auth.get_current_user`
- `app.api.routes.legacy.scalars.JSON`
- `app.api.session.get_db`
- `.logging_extension.LoggingExtension`
- `.mutations.Mutation`
- `.queries.Query`


# Global Variables

---
### graphql_router 
- **Type**: `GraphQLRouter`
- **Description**: The `graphql_router` is an instance of `GraphQLRouter` from the `strawberry.fastapi` module, which is configured with a GraphQL schema and a context getter function. It is used to handle GraphQL requests in a FastAPI application, providing the necessary schema and context for query execution.
- **Use**: This variable is used to route GraphQL requests within the FastAPI application, utilizing the defined schema and context.


---
### sandbox_router 
- **Type**: `GraphQLRouter`
- **Description**: The `sandbox_router` is an instance of `GraphQLRouter` configured to serve a GraphQL API using the Apollo Sandbox IDE. It is initialized with a predefined schema, a specific path for the Apollo Sandbox, and a context getter function to provide request-specific context.
- **Use**: This variable is used to handle GraphQL requests at the '/apollo-sandbox/' endpoint, utilizing the Apollo Sandbox IDE for testing and interaction.


---
### schema 
- **Type**: `strawberry.Schema`
- **Description**: The `schema` variable is an instance of `strawberry.Schema`, which is a GraphQL schema object created using the Strawberry library. It is configured with a query type, a mutation type, and additional settings such as disabling automatic camel case conversion and overriding the scalar type for dictionaries with a custom JSON scalar. The schema also includes extensions, such as the `LoggingExtension`, to enhance its functionality.
- **Use**: This variable is used to define the GraphQL schema for the application, specifying the queries, mutations, and configurations for the GraphQL API.


# Classes

---
### Context 
- **Type**: `class`
- **Members**:
    - `session`: Stores the database session for the context.
    - `user`: Holds the current user information for the context.
    - `m2m`: Contains the current machine-to-machine authentication details for the context.
- **Description**: The `Context` class is a specialized context object that extends the `BaseContext` class, designed to encapsulate session, user, and machine-to-machine (m2m) authentication details. It is used within a GraphQL API setup to provide necessary context for request handling, ensuring that each request has access to the current session, user, and m2m information.
- **Inherits From**:
    - BaseContext

**Methods**

---
#### Context.__init__
The `__init__` function initializes a `Context` object with session, user, and m2m attributes.
- **Inputs**:
    - `session`: A database session object used for database interactions.
    - `user`: The current user object, typically representing the authenticated user.
    - `m2m`: An object representing machine-to-machine authentication context.
- **Control Flow**:
    - Assigns the provided `session` argument to the `session` attribute of the `Context` instance.
    - Assigns the provided `user` argument to the `user` attribute of the `Context` instance.
    - Assigns the provided `m2m` argument to the `m2m` attribute of the `Context` instance.
    - Calls the `__init__` method of the superclass `BaseContext` to ensure proper initialization of the base class.
- **Output**:
    - This function does not return any value; it initializes the instance attributes of the `Context` class.



# Functions

---
### get_context 
The `get_context` function asynchronously creates and returns a `Context` object using dependencies for user, m2m, and database session.
- **Inputs**:
    - `user`: A dependency injection that provides the current user, obtained via the `get_current_user` function.
    - `m2m`: A dependency injection that provides the current machine-to-machine (m2m) context, obtained via the `get_current_m2m` function.
    - `session`: A dependency injection that provides the current database session, obtained via the `get_db` function.
- **Control Flow**:
    - The function is defined as asynchronous, allowing it to handle I/O-bound operations efficiently.
    - It uses FastAPI's `Depends` to inject dependencies for `user`, `m2m`, and `session`.
    - A `Context` object is instantiated with the injected `session`, `user`, and `m2m` values.
    - The newly created `Context` object is returned.
- **Output**:
    - The function returns a `Context` object initialized with the provided session, user, and m2m dependencies.


