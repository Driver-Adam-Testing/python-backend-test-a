# Purpose
This Python file is a FastAPI router module that provides API endpoints for managing subscription-related operations within an organization. It defines two main endpoints: one for retrieving the active subscription details of an organization and another for creating a new subscription. The module leverages FastAPI's `APIRouter` to organize these endpoints, making it a part of a larger web application structure. The endpoints are protected by permission dependencies, ensuring that only users with the appropriate permissions can access them. Specifically, the `get_active_subscription` endpoint requires `OrgManagerPermission`, while the `create_subscription` endpoint requires `SubscriptionManagerPermission`.

The code integrates with a billing service, as indicated by the use of the `BillingService` class, which handles the business logic for fetching and creating subscription records. The endpoints utilize data models such as `CreateSubscriptionRequest` and `SubscriptionRecord` to structure input and output data, ensuring consistency and validation. The file is designed to be part of a larger application, likely imported and used within a FastAPI application setup, and it defines a clear API interface for subscription management, making it a critical component of the application's billing functionality.
# Imports and Dependencies

---
- `fastapi`
- `shared.billing.billing_service`
- `shared.interfaces.billing.subscription_schema`
- `app.api.auth`
- `app.api.session`


# Global Variables

---
### router 
- **Type**: `APIRouter`
- **Description**: The `router` variable is an instance of FastAPI's `APIRouter` class. It is used to define a group of related API endpoints, which can be included in the main FastAPI application. This allows for modular and organized routing of HTTP requests.
- **Use**: The `router` is used to register HTTP endpoints for handling subscription-related operations, such as retrieving active subscription details and creating new subscriptions.


# Functions

---
### create_subscription 
The `create_subscription` function creates a new subscription for an organization using the provided session, token, and subscription request details.
- **Inputs**:
    - `session`: An instance of CurrentSession, representing the current session context.
    - `current_token`: An instance of M2MToken, representing the machine-to-machine authentication token.
    - `request`: An instance of CreateSubscriptionRequest, containing details about the subscription to be created, such as organization ID, plan type, billing frequency, and start date.
- **Control Flow**:
    - Check if the current_token is None; if so, raise an HTTPException with a 403 status code indicating 'Forbidden'.
    - Call the create_subscription method of the BillingService class, passing the session and details from the request to create a new subscription.
- **Output**:
    - Returns a SubscriptionRecord object representing the newly created subscription.


---
### get_active_subscription 
The function retrieves the active subscription for a user's organization from the billing service.
- **Inputs**:
    - `session`: An instance of CurrentSession, representing the current session context.
    - `user`: An instance of UserToken, representing the authenticated user, which includes the user's organization ID.
- **Control Flow**:
    - The function calls the method get_active_subscription_by_org on the BillingService instance, passing the user's organization ID to retrieve the active subscription.
    - If no active subscription is found, the function raises an HTTPException with a 404 status code and a message 'Subscription not found.'
    - If an active subscription is found, it is returned as the result of the function.
- **Output**:
    - The function returns a SubscriptionRecord object representing the active subscription for the user's organization.


