# Purpose
This Python file is a test script designed to validate the functionality of an AWS Lambda handler function, specifically focusing on its response to an SNS (Simple Notification Service) event. It uses the `pytest` framework to define a fixture, `sns_event`, which simulates an SNS event containing an S3 bucket notification. The test function `test_lambda_handler` invokes the `handler` function from the `src.main` module, passing the mock SNS event to it, and asserts that the response is "OK". This script provides narrow functionality, focusing solely on testing the correct handling of a specific type of event by the Lambda function, and it assumes that the necessary AWS environment and resources are appropriately mocked for testing purposes.
# Imports and Dependencies

---
- `json`
- `pytest`
- `httpx`
- `unittest`
- `src.main`
- `src.utils.config`


# Functions

---
### sns_event 
The `sns_event` function generates a mock AWS SNS event containing an S3 object creation notification.
- **Inputs**:
    - None
- **Control Flow**:
    - The function does not take any input parameters.
    - It returns a dictionary representing an SNS event with a single record.
    - The record contains an S3 event notification message, which is a JSON string.
    - The S3 event notification includes details such as event version, source, region, time, name, user identity, request parameters, response elements, schema version, configuration ID, bucket details, and object details.
- **Output**:
    - A dictionary representing a mock SNS event with an embedded S3 object creation notification message.


---
### test_lambda_handler 
The `test_lambda_handler` function tests the `handler` function by asserting that it returns 'OK' when given a mock SNS event.
- **Inputs**:
    - `sns_event`: A mock SNS event fixture that simulates an AWS SNS event with S3 object creation details.
- **Control Flow**:
    - The function calls the `handler` function with the `sns_event` and an empty dictionary as arguments.
    - It captures the response from the `handler` function.
    - An assertion checks if the response is equal to 'OK', raising an error if it is not.
- **Output**:
    - The function does not return any value; it raises an assertion error if the `handler` response is not 'OK'.


