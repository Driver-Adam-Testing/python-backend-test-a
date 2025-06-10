# Purpose
This code defines a set of data models using the Pydantic library, which is commonly used for data validation and settings management in Python. The file provides narrow functionality, specifically for handling user invitations and role modifications within a system. It includes models for an `Invitee` with an email, an `Invitation` that includes invitee details and a list of role IDs, and input models for creating invitations and modifying user roles. Additionally, it defines a response model for role modifications, detailing the user ID and lists of added and removed roles. This code is structured to ensure data integrity and validation for operations related to user invitations and role management.
# Imports and Dependencies

---
- `pydantic.BaseModel`
- `pydantic.EmailStr`
- `pydantic.Field`


# Global Variables

---
### roles 
- **Type**: `list`
- **Description**: The `roles` variable is a list of strings, where each string represents a role ID. It is used in multiple classes to define the roles associated with an invitation or a user.
- **Use**: This variable is used to store and manage role IDs in the context of invitations and user role modifications.


# Classes

---
### CreateInvitationInput 
- **Type**: `class`
- **Members**:
    - `invitations`: A list of Invitation objects to be created.
- **Description**: The CreateInvitationInput class is a Pydantic model that defines the structure for input data required to create multiple invitations. It contains a single attribute, 'invitations', which is a list of Invitation objects, each representing an invitation to be created with associated invitee and roles information.
- **Inherits From**:
    - BaseModel


---
### Invitation 
- **Type**: `class`
- **Members**:
    - `invitee`: An instance of the Invitee class representing the person being invited.
    - `roles`: A list of role IDs associated with the invitation.
- **Description**: The Invitation class is a data model that represents an invitation, consisting of an invitee and a list of role IDs. It is used to encapsulate the details of an invitation, including the person being invited and the roles they are being invited to assume. This class inherits from Pydantic's BaseModel, allowing for data validation and serialization.
- **Inherits From**:
    - BaseModel


---
### Invitee 
- **Type**: `class`
- **Members**:
    - `email`: An instance variable that stores the email address of the invitee, validated as an EmailStr.
- **Description**: The Invitee class is a simple data model that inherits from Pydantic's BaseModel. It is designed to represent an invitee with a single attribute, 'email', which is validated to ensure it is a properly formatted email address using Pydantic's EmailStr type.
- **Inherits From**:
    - BaseModel


---
### ModifyUserRolesInput 
- **Type**: `class`
- **Members**:
    - `roles`: A list of role IDs to be modified for a user.
- **Description**: The `ModifyUserRolesInput` class is a Pydantic model used to define the input structure for modifying user roles. It contains a single attribute, `roles`, which is a list of strings representing the role IDs that need to be modified. This class ensures that the input data adheres to the expected format and type constraints.
- **Inherits From**:
    - BaseModel


---
### ModifyUserRolesResponse 
- **Type**: `class`
- **Members**:
    - `user_id`: A string representing the unique identifier of the user whose roles are being modified.
    - `added_roles`: A list of strings representing the roles that have been added to the user.
    - `removed_roles`: A list of strings representing the roles that have been removed from the user.
- **Description**: The `ModifyUserRolesResponse` class is a data model that represents the response structure for modifying user roles, including the user's ID and lists of roles that were added or removed. It inherits from Pydantic's `BaseModel`, which provides data validation and serialization capabilities.
- **Inherits From**:
    - BaseModel


