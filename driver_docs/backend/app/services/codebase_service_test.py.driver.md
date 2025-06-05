# Purpose
This Python file is a test script utilizing the `pytest` framework to verify the functionality of two validation functions: `validate_codebase_analysis_presigned_url` and `validate_analyzed_codebase_object_key`, which are imported from the `app.services.codebase_service` module. The script contains two test functions, each designed to ensure that the respective validation function correctly authenticates or raises exceptions when provided with valid or invalid inputs. The tests focus on checking the proper handling of presigned URLs and object keys related to codebase analysis, specifically ensuring that unauthorized access attempts are correctly identified and handled by raising a `CodebaseAnalysisAuthException`. This code provides narrow functionality, specifically targeting the validation logic for codebase analysis security within a larger application.
# Imports and Dependencies

---
- `pytest`
- `app.services.codebase_service.CodebaseAnalysisAuthException`
- `app.services.codebase_service.validate_analyzed_codebase_object_key`
- `app.services.codebase_service.validate_codebase_analysis_presigned_url`


# Functions

---
### test_validate_analyzed_codebase_object_key 
The function `test_validate_analyzed_codebase_object_key` tests the `validate_analyzed_codebase_object_key` function to ensure it correctly validates codebase object keys against organization IDs and raises exceptions for invalid cases.
- **Inputs**:
    - None
- **Control Flow**:
    - Define a valid `codebase_object_key` and an invalid `bad_codebase_object_key`.
    - Call `validate_analyzed_codebase_object_key` with a valid key and organization ID to ensure no exception is raised.
    - Use `pytest.raises` to assert that `CodebaseAnalysisAuthException` is raised when the valid key is used with an incorrect organization ID.
    - Use `pytest.raises` to assert that `CodebaseAnalysisAuthException` is raised when the invalid key is used with the correct organization ID.
- **Output**:
    - The function does not return any value; it is a test function that asserts the correct behavior of `validate_analyzed_codebase_object_key` by raising exceptions when expected.


---
### test_validate_codebase_analysis_presigned_url 
The function `test_validate_codebase_analysis_presigned_url` tests the `validate_codebase_analysis_presigned_url` function for correct and incorrect authorization scenarios.
- **Inputs**:
    - None
- **Control Flow**:
    - A URL is defined for a codebase analysis presigned URL.
    - The `validate_codebase_analysis_presigned_url` function is called with the URL, a valid key ('analysis'), and a valid organization ID ('org_s76pU1v8LAYhTOWB') to test successful validation.
    - The function is called again with the same URL and key but an invalid organization ID ('org_id'), expecting a `CodebaseAnalysisAuthException` to be raised.
    - The function is called a third time with the same URL and organization ID but an invalid key ('key'), again expecting a `CodebaseAnalysisAuthException` to be raised.
- **Output**:
    - The function does not return any value; it is used to assert that the `validate_codebase_analysis_presigned_url` function behaves correctly under different authorization scenarios.


