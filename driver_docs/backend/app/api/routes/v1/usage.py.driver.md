# Purpose
This Python file is a FastAPI router module that defines a set of API endpoints related to usage management, specifically for handling usage balance, usage summaries, recent usage charges, and issuing usage credits. The module imports various components from other parts of the application, such as models, services, and utilities, to facilitate these operations. The endpoints are designed to interact with a `UsageService` class, which is responsible for retrieving and manipulating usage data. The endpoints include `GET` requests for fetching usage balance summaries, detailed usage summaries, and recent usage charges, as well as a `POST` request for issuing usage credits. The `POST` request also integrates with AWS services to handle event management, indicating a reliance on external cloud infrastructure.

The file is structured to provide a clear API interface for usage-related operations, making it a critical component of a larger application that likely deals with resource usage tracking and management. The use of FastAPI's routing and dependency injection features, such as `APIRouter`, `Query`, and `HTTPException`, suggests that this module is part of a web service that requires authentication and authorization, as indicated by the use of tokens and permissions. The endpoints are designed to be consumed by clients that need to manage and monitor usage data, making this module a key part of the application's public API.
# Imports and Dependencies

---
- `datetime`
- `boto3`
- `database.models_v1.UsageEventType`
- `fastapi.APIRouter`
- `fastapi.HTTPException`
- `fastapi.Query`
- `fastapi.status`
- `fastapi.responses.JSONResponse`
- `shared.interfaces.usage.usage_schema.CreditUsageEvent`
- `shared.interfaces.usage.usage_schema.UsageBalance`
- `shared.interfaces.usage.usage_schema.UsageCharge`
- `shared.interfaces.usage.usage_schema.UsageEventSummary`
- `shared.usage.usage_service.UsageService`
- `shared.usage.utils.sloc_to_bytes`
- `app.api.auth.M2MToken`
- `app.api.auth.UsageCreditPermission`
- `app.api.auth.UserToken`
- `app.api.routes.v2.query_utils.Pagination`
- `app.api.session.CurrentSession`
- `app.core.config.settings`


# Global Variables

---
### router 
- **Type**: `APIRouter`
- **Description**: The `router` variable is an instance of FastAPI's `APIRouter` class. It is used to define a group of related API endpoints for handling HTTP requests related to usage balance, usage summary, usage charges, and issuing usage credits.
- **Use**: This variable is used to register and organize API routes for the application, allowing for modular and maintainable code.


# Functions

---
### credit_usage 
The `credit_usage` function issues usage credits to an organization based on a credit usage event, using AWS services for event handling.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current database session.
    - `current_token`: An instance of `M2MToken` representing the current machine-to-machine authentication token.
    - `credit_usage_event`: An instance of `CreditUsageEvent` containing details about the credit usage event, including organization ID and SLOC credit amount.
- **Control Flow**:
    - Check if `current_token` is `None` and raise an HTTP 403 Forbidden exception if true.
    - Initialize an AWS client for the 'events' service using credentials from settings.
    - Extract `organization_id` and `user_id` from `credit_usage_event`, defaulting `user_id` to 'SYSTEM' if not provided.
    - Set `event_type` to `UsageEventType.BASE_PLATFORM_USAGE_CREDIT`.
    - Convert `sloc_credit_amount` from `credit_usage_event` to bytes using `sloc_to_bytes`.
    - Call `issue_usage_credits` on `UsageService` with the session, AWS client, organization ID, user ID, event type, and credit amount.
    - Return a JSON response with status code 202 and a message indicating acceptance.
- **Output**:
    - A `JSONResponse` with status code 202 and a message indicating the request was accepted.


---
### get_charges 
The `get_charges` function retrieves a list of recent usage charges for a user's organization with pagination and sorting options.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current database session.
    - `user`: An instance of `UserToken` containing user authentication information, including the organization ID.
    - `pagination`: An instance of `Pagination` containing pagination parameters such as limit, offset, and sort direction.
- **Control Flow**:
    - Extracts the `limit`, `offset`, and `sort_direction` from the `pagination` object.
    - Calls the `get_charges` method of the `UsageService` class, passing the user's organization ID and the extracted pagination parameters.
    - Returns the result of the `get_charges` method call, which is a list of `UsageCharge` objects.
- **Output**:
    - A list of `UsageCharge` objects representing the recent usage charges for the user's organization.


---
### get_usage_balance 
The `get_usage_balance` function retrieves the usage balance for a user's organization using a session and user token.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current session context.
    - `user`: An instance of `UserToken` representing the authenticated user, which includes the user's organization ID.
- **Control Flow**:
    - Initialize a `UsageService` object with the provided session.
    - Extract the organization ID from the user token.
    - Call the `get_usage_balance` method of the `UsageService` object with the organization ID to retrieve the usage balance.
    - Return the retrieved usage balance.
- **Output**:
    - The function returns an instance of `UsageBalance`, which represents the usage balance for the specified organization.


---
### get_usage_summary 
The `get_usage_summary` function retrieves a detailed usage summary for a user's organization within an optional date range.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current database session.
    - `user`: An instance of `UserToken` representing the authenticated user, which includes the user's organization ID.
    - `start_date`: An optional `datetime` object specifying the start date for the usage summary query, defaulting to `None`.
    - `end_date`: An optional `datetime` object specifying the end date for the usage summary query, defaulting to `None`.
- **Control Flow**:
    - Initialize a `UsageService` object with the provided `session`.
    - Extract the `organization_id` from the `user` object.
    - Call the `get_usage_summary` method of the `UsageService` object, passing the `organization_id`, `start_date`, and `end_date`.
    - Return the result of the `get_usage_summary` method call.
- **Output**:
    - The function returns an instance of `UsageEventSummary`, which contains the detailed usage summary for the specified organization and date range.


