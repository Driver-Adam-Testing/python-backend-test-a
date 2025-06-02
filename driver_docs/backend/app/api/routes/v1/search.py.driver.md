# Purpose
This code defines a FastAPI router for handling a search operation within a web application. It provides narrow functionality, specifically focusing on a single endpoint that allows users to search for content. The code imports necessary components such as `SearchInput` and `SearchResults` for handling search data, and `search_content` for executing the search logic. It also includes authentication and session management through `ContentReadonlyPermission` and `UserToken`, ensuring that only authorized users can perform the search. The `search` function modifies the search input to include the user's organization ID before invoking the search pipeline, indicating a need for further refinement as noted by the TODO comment.
# Imports and Dependencies

---
- `fastapi.APIRouter`
- `shared.interfaces.search.SearchInput`
- `shared.interfaces.search.SearchResults`
- `shared.pipelines.search.search_content`
- `app.api.auth.ContentReadonlyPermission`
- `app.api.auth.UserToken`
- `app.api.session.CurrentSession`


# Global Variables

---
### router 
- **Type**: `APIRouter`
- **Description**: The `router` variable is an instance of FastAPI's `APIRouter` class. It is used to define a group of related API routes and their associated request handlers. This allows for modular and organized route management within a FastAPI application.
- **Use**: The `router` is used to register API endpoints and their configurations, such as HTTP methods, paths, and dependencies, for the application.


# Functions

---
### search 
The `search` function modifies the search input with the user's organization ID and delegates the search operation to the `search_content` function.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current session context.
    - `user`: An instance of `UserToken` representing the authenticated user, which includes user-specific information such as organization ID.
    - `input`: An instance of `SearchInput` containing the parameters for the search operation.
- **Control Flow**:
    - The function begins by setting the `organization_id` attribute of the `input` object to the `organization_id` of the `user` object.
    - It then calls the `search_content` function, passing the `session` and modified `input` as arguments.
    - The result from `search_content` is returned as the output of the function.
- **Output**:
    - The function returns a `SearchResults` object, which contains the results of the search operation.


