# Purpose
This Python code defines a set of data models and utility functions for managing and converting usage metrics related to software usage events. The code is structured using Pydantic's `BaseModel` to define data models that represent different aspects of usage tracking, such as `CreditUsageEvent`, `UsageBalance`, `UsageEventSummary`, `UsageCharge`, and `UsageEventRange`. These models encapsulate information about usage credits, debits, and events, and provide methods for converting between different units of measurement, specifically between "bytes" and "sloc" (source lines of code). The `UsageMetricUnitType` enumeration defines the possible units for these conversions.

The code is designed to be part of a larger system, likely a backend service, that tracks and manages usage metrics for an organization or platform. It includes validation logic to ensure that date fields are timezone-aware, which is crucial for accurate time-based calculations. The models are configured to be immutable (frozen), ensuring that once an instance is created, its state cannot be altered, which is a common practice for data integrity in financial or usage tracking systems. The code does not define a public API or external interfaces directly but provides foundational components that can be used by other parts of the system to handle usage data consistently and accurately.
# Imports and Dependencies

---
- `datetime`
- `enum`
- `database.models_v1`
- `pydantic`
- `shared.usage.utils`


# Global Variables

---
### BYTES 
- **Type**: `str`
- **Description**: `BYTES` is a member of the `UsageMetricUnitType` enumeration, representing a unit of measurement for usage metrics in terms of bytes. It is used to specify that the usage data should be interpreted or converted in terms of bytes.
- **Use**: This variable is used to define the unit type for usage metrics, allowing for conversion and interpretation of usage data in terms of bytes.


---
### SLOC 
- **Type**: ``str``
- **Description**: `SLOC` is a string value representing a unit type in the `UsageMetricUnitType` enumeration. It stands for Source Lines of Code, which is a metric used to measure the size of a software program by counting the number of lines in its source code.
- **Use**: `SLOC` is used as a unit type to specify and convert usage metrics in the context of software usage tracking and billing.


---
### bytes 
- **Type**: `int`
- **Description**: The `bytes` variable is an integer field within the `UsageCharge` class, representing the number of bytes associated with a particular usage charge event. It is marked with `Field(exclude=True)`, indicating that it is excluded from certain operations, such as serialization or validation, by default.
- **Use**: This variable is used to store the byte count for a usage charge, which can be converted to source lines of code (SLOC) using the `bytes_to_sloc` function.


---
### end_date 
- **Type**: `datetime | None`
- **Description**: The `end_date` variable is a global variable defined within the `UsageEventRange` class. It represents the end date of a usage event range and is of type `datetime` or `None`, allowing for optional specification of the end date.
- **Use**: This variable is used to store the end date of a usage event range and is validated to ensure it is timezone-aware.


---
### event_type 
- **Type**: `UsageEventType`
- **Description**: The `event_type` variable is an instance of the `UsageEventType` enumeration, which is imported from the `database.models_v1` module. It represents the type of usage event that has occurred, such as onboarding, code diff, or platform usage credit.
- **Use**: This variable is used to categorize and identify the specific type of usage event in the `UsageCharge` class.


---
### frozen 
- **Type**: `bool`
- **Description**: The `frozen` variable is a configuration setting within the `Config` class of the `UsageBalance` and `UsageEventSummary` classes. It is a boolean value that, when set to `True`, makes the instances of these classes immutable after they are created.
- **Use**: This variable is used to ensure that instances of `UsageBalance` and `UsageEventSummary` cannot be modified after their creation, providing data integrity and consistency.


---
### start_date 
- **Type**: `datetime | None`
- **Description**: The `start_date` variable is a field in the `UsageEventRange` class, which is a subclass of `BaseModel`. It is intended to represent the starting date of a usage event range and can be either a `datetime` object or `None`. The variable is validated to ensure it is timezone-aware, requiring the use of ISO 8601 format.
- **Use**: This variable is used to define the beginning of a range for usage events, ensuring that the date is properly formatted and timezone-aware.


---
### user_id 
- **Type**: `str | None`
- **Description**: The `user_id` variable is an optional string attribute within the `CreditUsageEvent` class, which is a subclass of `BaseModel`. It represents the unique identifier for a user associated with a credit usage event.
- **Use**: This variable is used to store the user identifier for tracking and associating credit usage events with specific users.


# Classes

---
### Config 
- **Type**: `class`
- **Members**:
    - `frozen`: A class variable indicating that instances of the class are immutable.
- **Description**: The `Config` class is a simple configuration class with a single class variable `frozen` set to `True`, indicating that instances of the class are intended to be immutable. This class is used as a configuration for other classes, such as `UsageBalance` and `UsageEventSummary`, to enforce immutability.


---
### CreditUsageEvent 
- **Type**: `class`
- **Members**:
    - `sloc_credit_amount`: The amount of source lines of code (SLOC) credits used.
    - `organization_id`: The identifier for the organization associated with the credit usage event.
    - `user_id`: The identifier for the user associated with the credit usage event, which can be None.
- **Description**: The `CreditUsageEvent` class is a data model that represents an event where SLOC credits are used by an organization, optionally associated with a specific user. It is a simple model with three attributes: `sloc_credit_amount` to track the number of SLOC credits used, `organization_id` to identify the organization involved, and `user_id` to optionally identify the user involved in the event. This class inherits from Pydantic's `BaseModel`, providing data validation and serialization capabilities.
- **Inherits From**:
    - BaseModel


---
### UsageBalance 
- **Type**: `class`
- **Members**:
    - `credits`: The number of credits in the usage balance.
    - `debits`: The number of debits in the usage balance.
    - `unit`: The unit of measurement for the usage balance, either bytes or sloc.
    - `balance`: A computed property that returns the net balance by subtracting debits from credits.
- **Description**: The `UsageBalance` class is a model that represents a balance of usage credits and debits, measured in a specified unit of either bytes or source lines of code (SLOC). It provides a computed property to calculate the net balance and a method to convert the credits, debits, and balance to a different unit. The class is immutable, as indicated by the frozen configuration in its Pydantic model configuration.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### UsageBalance.balance
The `balance` function calculates the net balance by subtracting debits from credits.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the result of subtracting the `debits` attribute from the `credits` attribute.
- **Output**:
    - The function returns an integer representing the net balance.


---
#### UsageBalance.convert_to
The `convert_to` function converts the credits, debits, and balance of a `UsageBalance` object to a specified unit type.
- **Inputs**:
    - `target_unit`: The target unit type to which the credits, debits, and balance should be converted, specified as a `UsageMetricUnitType`.
- **Control Flow**:
    - Check if the current unit of the `UsageBalance` object is the same as the `target_unit`; if so, return the current object without changes.
    - Determine the appropriate conversion function (`sloc_to_bytes` or `bytes_to_sloc`) based on the `target_unit`.
    - Apply the conversion function to the `credits` and `debits` of the `UsageBalance` object to obtain `new_credits` and `new_debits`.
    - Return a new `UsageBalance` object with the converted `credits`, `debits`, and the specified `target_unit`.
- **Output**:
    - A new `UsageBalance` object with credits and debits converted to the specified `target_unit`.


**Nested Classes**
    - Config


---
### UsageCharge 
- **Type**: `class`
- **Members**:
    - `asset_name`: The name of the asset associated with the usage charge.
    - `timestamp`: The date and time when the usage charge was recorded.
    - `bytes`: The number of bytes used, excluded from the model by default.
    - `event_type`: The type of usage event, excluded from the model by default.
    - `sloc`: The source lines of code equivalent of the bytes used.
    - `change_type`: The type of change associated with the usage event, derived from the event type.
- **Description**: The `UsageCharge` class is a model that represents a charge based on usage metrics, specifically tracking the asset name, timestamp, and usage in bytes. It includes computed properties to convert bytes to source lines of code (SLOC) and to determine the type of change based on the usage event type. The class uses Pydantic's `BaseModel` for data validation and management, and it excludes certain fields from the model by default.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### UsageCharge.change_type
The `change_type` function returns a string representing the type of change associated with a specific usage event type.
- **Inputs**:
    - `self`: An instance of the class containing the `change_type` method, which includes an `event_type` attribute of type `UsageEventType`.
- **Control Flow**:
    - The function uses a dictionary to map specific `UsageEventType` values to corresponding change type strings ('new', 'update', 'add').
    - It retrieves the change type string by using the `event_type` attribute of the `self` object as the key in the dictionary.
    - If the `event_type` is not found in the dictionary, the function returns 'unknown' as the default value.
- **Output**:
    - A string indicating the type of change ('new', 'update', 'add', or 'unknown') based on the `event_type`.


---
#### UsageCharge.sloc
The `sloc` function converts the `bytes` attribute of a `UsageCharge` instance to source lines of code (SLOC) using the `bytes_to_sloc` utility function.
- **Inputs**:
    - `self`: An instance of the `UsageCharge` class, which contains the `bytes` attribute to be converted to SLOC.
- **Control Flow**:
    - The function accesses the `bytes` attribute of the `UsageCharge` instance.
    - It calls the `bytes_to_sloc` function, passing the `bytes` attribute as an argument.
    - The result of the conversion is returned as the output of the function.
- **Output**:
    - An integer representing the source lines of code (SLOC) equivalent of the `bytes` attribute.



---
### UsageEventRange 
- **Type**: `class`
- **Members**:
    - `start_date`: Optional datetime representing the start of the usage event range.
    - `end_date`: Optional datetime representing the end of the usage event range.
- **Description**: The `UsageEventRange` class is a Pydantic model that represents a range of usage events with optional start and end dates. It includes validators to ensure that both `start_date` and `end_date`, if provided, are timezone-aware, adhering to the ISO 8601 format. This class is useful for defining a time period over which usage events are considered, ensuring that the dates are correctly formatted and include timezone information.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### UsageEventRange.validate_end_date
The `validate_end_date` function ensures that the `end_date` in a dictionary is timezone-aware.
- **Inputs**:
    - `values`: A dictionary containing the data to be validated, specifically looking for an 'end_date' key.
- **Control Flow**:
    - Retrieve the 'end_date' from the 'values' dictionary.
    - Check if 'end_date' is present and if it is not timezone-aware (i.e., 'tzinfo' is None).
    - If 'end_date' is not timezone-aware, raise a ValueError with a specific message.
    - Return the 'values' dictionary if no error is raised.
- **Output**:
    - The function returns the input dictionary 'values' if the 'end_date' is valid.


---
#### UsageEventRange.validate_start_date
The `validate_start_date` function ensures that the `start_date` in the input dictionary is timezone-aware.
- **Inputs**:
    - `values`: A dictionary containing the data to be validated, expected to have a 'start_date' key with a datetime value.
- **Control Flow**:
    - Retrieve the 'start_date' from the input dictionary 'values'.
    - Check if 'start_date' is not None and if it lacks timezone information (tzinfo is None).
    - If 'start_date' is not timezone-aware, raise a ValueError with a specific message.
    - Return the input dictionary 'values' if no error is raised.
- **Output**:
    - The function returns the input dictionary 'values' if the 'start_date' is valid.



---
### UsageEventSummary 
- **Type**: `class`
- **Members**:
    - `onboarding_usage`: Tracks the usage count for onboarding activities.
    - `tech_doc_usage`: Tracks the usage count for technical documentation activities.
    - `code_diff_usage`: Tracks the usage count for code difference activities.
    - `agent_pipeline_usage`: Tracks the usage count for agent pipeline activities.
    - `pdf_summarization_usage`: Tracks the usage count for PDF summarization activities.
    - `platform_usage_credits`: Tracks the number of platform usage credits consumed.
    - `user_seat_count`: Tracks the number of user seats involved in the usage.
    - `unit`: Specifies the unit of measurement for usage metrics.
- **Description**: The `UsageEventSummary` class is a data model that summarizes usage events by different types, such as onboarding, technical documentation, code differences, agent pipelines, and PDF summarization. It includes attributes to track the usage counts for each type, the number of platform usage credits, and the user seat count. The class provides a method to convert these usage values to a specified unit, either bytes or SLOC (Source Lines of Code), using conversion functions. The class is immutable, as indicated by the frozen configuration.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### UsageEventSummary.convert_to
The `convert_to` function converts usage values in a `UsageEventSummary` object to a specified unit type.
- **Inputs**:
    - `target_unit`: The target unit type to which the usage values should be converted, specified as a `UsageMetricUnitType` (either `BYTES` or `SLOC`).
- **Control Flow**:
    - Check if the current unit of the `UsageEventSummary` object is the same as the `target_unit`; if so, return the object itself without any conversion.
    - Determine the appropriate conversion function (`sloc_to_bytes` or `bytes_to_sloc`) based on the `target_unit`.
    - Apply the conversion function to each usage attribute (`onboarding_usage`, `tech_doc_usage`, `code_diff_usage`, `agent_pipeline_usage`, `pdf_summarization_usage`, and `platform_usage_credits`).
    - Create and return a new `UsageEventSummary` object with the converted usage values and the `target_unit`.
- **Output**:
    - A new `UsageEventSummary` object with usage values converted to the specified `target_unit`.


**Nested Classes**
    - Config


---
### UsageMetricUnitType 
- **Type**: `class`
- **Members**:
    - `BYTES`: Represents the unit type 'bytes'.
    - `SLOC`: Represents the unit type 'sloc'.
- **Description**: The `UsageMetricUnitType` class is an enumeration that defines two types of usage metric units: 'bytes' and 'sloc' (source lines of code). It inherits from both `str` and `Enum`, allowing it to be used as a string while also providing enumeration capabilities. This class is used to specify the unit of measurement for usage metrics in the system.
- **Inherits From**:
    - str
    - Enum


