# Purpose
This Python file is a test configuration script using the `pytest` framework, providing narrowly focused functionality for setting up test fixtures. It defines three fixtures: `db`, `current_user_with_org`, and `current_user_with_other_org`. The `db` fixture manages a database session using SQLModel, ensuring that each test function has access to a fresh session without altering the database schema, as indicated by the commented-out `create_all` and `drop_all` calls. The other two fixtures, `current_user_with_org` and `current_user_with_other_org`, use the `unittest.mock` library to create mock `UserToken` objects, simulating different user contexts for testing purposes. This setup facilitates isolated and repeatable tests by providing controlled environments and mock data.
# Imports and Dependencies

---
- `collections.abc`
- `unittest.mock`
- `pytest`
- `database.db`
- `sqlmodel`
- `app.api.auth`


# Functions

---
### current_user_with_org 
The `current_user_with_org` function creates and returns a mock `UserToken` object with predefined user and organization attributes for testing purposes.
- **Inputs**:
    - None
- **Control Flow**:
    - A mock object `current_user` is created with the specification of the `UserToken` class.
    - The `user_id` attribute of `current_user` is set to 'test_user_id'.
    - The `organization_id` attribute of `current_user` is set to 'test_org_id'.
    - The `organization_name` attribute of `current_user` is set to 'test_org_name'.
    - The `is_service_account` attribute of `current_user` is set to `False`.
    - The `current_user` mock object is returned.
- **Output**:
    - The function returns a mock `UserToken` object with predefined attributes for user and organization.


---
### current_user_with_other_org 
The function `current_user_with_other_org` creates and returns a mock `UserToken` object representing a user associated with a different organization for testing purposes.
- **Inputs**:
    - None
- **Control Flow**:
    - A mock object `current_user` is created with the specification of the `UserToken` class.
    - The `user_id` attribute of `current_user` is set to 'other_test_user_id'.
    - The `organization_id` attribute of `current_user` is set to 'other_test_org_id'.
    - The `organization_name` attribute of `current_user` is set to 'other_test_org_name'.
    - The `is_service_account` attribute of `current_user` is set to `False`.
    - The `current_user` mock object is returned.
- **Output**:
    - The function returns a mock `UserToken` object with predefined attributes for testing.


---
### db 
The `db` function is a pytest fixture that provides a SQLModel session for database operations during testing.
- **Inputs**:
    - None
- **Control Flow**:
    - The function is defined as a pytest fixture with a scope of 'function', meaning it is set up and torn down for each test function.
    - The function begins by creating a session using the SQLModel `Session` class with the provided `engine`.
    - The session is yielded, allowing the test to perform database operations within the context of this session.
    - After the test completes, the session context is exited, automatically handling session closure.
- **Output**:
    - The function yields a `Session` object for interacting with the database during tests.


