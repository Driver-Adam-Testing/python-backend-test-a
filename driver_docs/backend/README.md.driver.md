# Purpose
The provided content is a comprehensive documentation file for setting up and managing a FastAPI project backend using Docker and Poetry. This file serves as a guide for developers to configure their local development environment, detailing the necessary tools and steps to start the application stack using Docker Compose. It covers various aspects of the development workflow, including dependency management with Poetry, code modification, and testing procedures using Pytest. The document also explains how to handle database migrations with Alembic and provides instructions for using Visual Studio Code for debugging and testing. The content is crucial for developers working on the codebase, as it ensures a consistent and efficient development process by outlining the setup and operational procedures for the backend environment.
# Content Summary
This document serves as a comprehensive guide for setting up and managing a FastAPI project backend, particularly focusing on local development using Docker and Poetry. It outlines the necessary tools and steps for developers to efficiently work with the project.

### Key Components:

1. **Requirements**: 
   - The project requires Docker for containerization and Poetry for Python package and environment management.

2. **Local Development Setup**:
   - Developers can start the application stack using Docker Compose with the command `docker compose up -d`. This setup includes various services accessible via specific URLs:
     - Frontend: `http://localhost`
     - Backend API: `http://localhost/api/`
     - Swagger UI for API documentation: `http://localhost/docs`
     - Adminer for database management: `http://localhost:8080`
     - Traefik UI for route management: `http://localhost:8090`

3. **Backend Development Workflow**:
   - Dependencies are managed with Poetry, and developers can install them using `poetry install` and start a shell session with `poetry shell`.
   - Code modifications are made in specific directories for models, API endpoints, and CRUD utilities.
   - VS Code is pre-configured for debugging and running tests.

4. **Docker Compose Override**:
   - The `docker-compose.override.yml` file allows developers to make changes that only affect the local development environment. This includes mounting the backend code as a host volume for live updates and using a command override to enable live reloading of the server.

5. **Testing**:
   - Backend tests are executed using Pytest, with scripts provided to facilitate test execution. Test coverage reports are generated in `htmlcov/index.html`.
   - Developers can run tests directly within the Docker container using `docker compose exec backend bash /app/tests-start.sh`.

6. **Database Migrations**:
   - Alembic is used for database migrations, with commands provided to create and apply migrations. Developers are advised to commit migration files to the git repository.
   - Instructions are given for handling migrations, including creating revisions and upgrading the database schema.

7. **Unit Testing**:
   - Unit tests can be run using the command `pytest -m unit`.

This document is essential for developers to understand the setup, development, and testing processes for the FastAPI backend, ensuring a smooth workflow and efficient management of the development environment.
