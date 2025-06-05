# Purpose
This Python file is a configuration script for setting up API routing in a web application using the FastAPI framework. It defines an `APIRouter` instance, `api_router`, which aggregates various route modules from different parts of the application. The file imports route modules from both legacy and versioned directories, indicating a structured approach to managing API endpoints across different versions and functionalities. The routes are organized under specific prefixes and tags, which help in categorizing and accessing them efficiently. For instance, routes related to user management, content, and search are included with their respective prefixes and tags, facilitating clear API documentation and usage.

The script also includes conditional logic to incorporate a sandbox environment for non-production settings, demonstrating an environment-aware configuration. This file serves as a central point for API route management, ensuring that all endpoints are registered and accessible through a unified router. It does not define public APIs directly but rather organizes and exposes them through the included routers, making it a crucial component in the backend infrastructure of the application. The use of tags and prefixes aids in maintaining a clean and organized API structure, which is essential for both development and client interaction.
# Imports and Dependencies

---
- `fastapi`
- `app.api.routes.legacy.schema`
- `app.api.routes.v1.agent_pipelines`
- `app.api.routes.v1.codebase`
- `app.api.routes.v1.content`
- `app.api.routes.v1.git_provider`
- `app.api.routes.v1.healthcheck`
- `app.api.routes.v1.onboarding`
- `app.api.routes.v1.organization`
- `app.api.routes.v1.search`
- `app.api.routes.v1.subscription`
- `app.api.routes.v1.tags`
- `app.api.routes.v1.upload`
- `app.api.routes.v1.usage`
- `app.api.routes.v1.user`
- `app.api.routes.v2.autodocs`
- `app.api.routes.v2.chat`
- `app.api.routes.v2.contents`
- `app.api.routes.v2.convenience_endpoints`
- `app.api.routes.v2.document_sources`
- `app.api.routes.v2.generate`
- `app.api.routes.v2.nodes`
- `app.api.routes.v2.primary_asset_tags`
- `app.api.routes.v2.primary_assets`
- `app.api.routes.v2.versions`
- `app.api.routes.v2.router`
- `app.api.routes.v2.tags`
- `app.core.config`


# Global Variables

---
### api_router 
- **Type**: `APIRouter`
- **Description**: The `api_router` is an instance of FastAPI's `APIRouter` class, which is used to define and organize the routes for the API. It aggregates multiple route modules, each with its own prefix and tags, to create a comprehensive routing structure for the application.
- **Use**: The `api_router` is used to include various route modules, each with specific prefixes and tags, to manage the API's endpoints and their organization.


