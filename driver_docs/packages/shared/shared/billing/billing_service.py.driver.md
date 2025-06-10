# Purpose
The provided code defines a service class, `BillingService`, which is part of a larger application dealing with subscription management. This class is designed to interact with a database to manage subscription records for organizations. It provides methods to retrieve active subscriptions and create new subscriptions, ensuring that an organization cannot have more than one active subscription at a time. The class uses SQLModel for database interactions and relies on a `BaseRepository` for executing queries. The `BillingService` class is initialized with a database session, which it uses to perform operations on the `Subscription` model.

The code is structured as a library component intended to be integrated into a larger system, rather than a standalone script. It defines a public API through its methods, `get_active_subscription_by_org` and `create_subscription`, which are likely to be used by other parts of the application to manage subscription data. The code also includes error handling through a custom exception, `SubscriptionServiceError`, to manage cases where an organization attempts to create a duplicate active subscription. This file is a focused implementation, providing specific functionality related to billing and subscription management within the broader application context.
# Imports and Dependencies

---
- `datetime.UTC`
- `datetime.datetime`
- `app.core.logger.logger`
- `database.models_v1.BillingFrequency`
- `database.models_v1.PlanType`
- `database.models_v1.Subscription`
- `database.models_v1.SubscriptionStatus`
- `sqlmodel.Session`
- `shared.interfaces.billing.subscription_schema.SubscriptionRecord`
- `shared.repositories.base_repository.BaseRepository`


# Classes

---
### BillingService 
- **Type**: `class`
- **Members**:
    - `session`: Holds the database session for executing queries.
    - `subscription_repository`: Manages subscription data access using a base repository pattern.
- **Description**: The `BillingService` class provides methods to manage subscription-related operations, such as retrieving active subscriptions for an organization and creating new subscriptions. It utilizes a session for database interactions and a repository pattern for accessing subscription data. The class ensures that an organization cannot have more than one active subscription at a time, raising an error if a new subscription is attempted while one is already active.

**Methods**

---
#### BillingService.__init__
The `__init__` function initializes a `BillingService` instance with a database session and a subscription repository.
- **Inputs**:
    - `self`: A reference to the current instance of the `BillingService` class.
    - `session`: An instance of `Session` used to interact with the database.
- **Control Flow**:
    - Assigns the provided `session` to the instance variable `self.session`.
    - Initializes `self.subscription_repository` with a `BaseRepository` instance, passing the `session` and `Subscription` model.
- **Output**:
    - The function does not return any value; it initializes the instance variables.


---
#### BillingService.create_subscription
The `create_subscription` function creates a new subscription for an organization if no active subscription exists.
- **Inputs**:
    - `self`: An instance of the `BillingService` class, which provides access to the session and subscription repository.
    - `organization_id`: A string representing the unique identifier of the organization for which the subscription is being created.
    - `plan_type`: An instance of `PlanType` indicating the type of subscription plan.
    - `billing_frequency`: An instance of `BillingFrequency` specifying how often the billing occurs.
    - `start_date`: An optional `datetime` object representing the start date of the subscription; defaults to the current date and time if not provided.
- **Control Flow**:
    - The function first checks if there is an active subscription for the given organization by calling `get_active_subscription_by_org` with `organization_id`.
    - If an active subscription is found, it logs an informational message and raises a `SubscriptionServiceError` to prevent creating a duplicate subscription.
    - If no active subscription exists, it creates a new `Subscription` object with the provided details, using the current date and time as the creation date if `start_date` is not specified.
    - The new subscription is added to the session, committed to the database, and refreshed to ensure it is up-to-date.
    - Finally, the function returns a `SubscriptionRecord` object created from the new subscription's data.
- **Output**:
    - The function returns a `SubscriptionRecord` object representing the newly created subscription.


---
#### BillingService.get_active_subscription_by_org
The function retrieves the active subscription record for a given organization from the database.
- **Inputs**:
    - `self`: An instance of the BillingService class, which provides access to the subscription repository.
    - `organization_id`: A string representing the unique identifier of the organization for which the active subscription is being queried.
- **Control Flow**:
    - The function calls the `get_by_conditions` method of the `subscription_repository` to query the database for a subscription that matches the given `organization_id` and has a status of `ACTIVE`.
    - If no subscription is found, the function returns `None`.
    - If a subscription is found, it converts the subscription data into a `SubscriptionRecord` object using the `model_dump` method and returns it.
- **Output**:
    - The function returns a `SubscriptionRecord` object representing the active subscription for the specified organization, or `None` if no active subscription is found.



---
### SubscriptionServiceError 
- **Type**: `class`
- **Description**: The `SubscriptionServiceError` class is a custom exception that inherits from Python's built-in `Exception` class. It is used to signal errors specific to the subscription service, such as when an organization already has an active subscription.
- **Inherits From**:
    - Exception


