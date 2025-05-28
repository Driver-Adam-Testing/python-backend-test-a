# Purpose
This Python file defines a class `TestInDevStack`, which is a specialized AWS Cloud Development Kit (CDK) stack intended for temporary deployment of additional infrastructure in a development environment. The code provides narrow functionality, focusing on setting up a specific AWS Lambda function for metrics collection, using parameters such as environment and database URL sourced from environment variables. The stack is designed for manual deployment to facilitate testing alongside existing resources, with the expectation that it will be discarded after its purpose is fulfilled. This file is a part of a larger infrastructure-as-code setup, leveraging the AWS CDK to manage cloud resources programmatically.
# Imports and Dependencies

---
- `os`
- `aws_cdk.Stack`
- `constructs.Construct`
- `cdk.constructs.metrics_lambda.MetricsLambda`
- `cdk.constructs.metrics_lambda.MetricsLambdaParams`


# Classes

---
### TestInDevStack 
- **Type**: `class`
- **Members**:
    - `metrics_lambda`: An instance of MetricsLambda initialized with environment and database URL parameters.
- **Description**: The `TestInDevStack` class is a specialized AWS CDK stack designed for deploying additional infrastructure components for testing purposes in a development environment. It inherits from the `Stack` class and initializes a `MetricsLambda` instance, which is configured using environment variables for the environment and database URL. This stack is intended for temporary use and may be deleted after its purpose is fulfilled.
- **Inherits From**:
    - Stack

**Methods**

---
#### TestInDevStack.__init__
The __init__ function initializes a TestInDevStack object, setting up a MetricsLambda with environment and database URL parameters.
- **Inputs**:
    - `scope`: A Construct object that defines the scope in which this stack is created.
    - `construct_id`: A string that uniquely identifies this construct within its scope.
    - `kwargs`: Additional keyword arguments that are passed to the parent class initializer.
- **Control Flow**:
    - The function begins by calling the parent class's __init__ method with the provided scope, construct_id, and any additional keyword arguments.
    - It then initializes a MetricsLambda object, passing itself as the scope, a string identifier 'MetricsLambda', and a MetricsLambdaParams object.
    - The MetricsLambdaParams object is initialized with environment and database_url parameters, which are retrieved from environment variables 'ENVIRONMENT' and 'DATABASE_URL', respectively, with a default value of 'development' for the environment.
- **Output**:
    - The function does not return any value; it initializes the TestInDevStack object with a metrics_lambda attribute.



