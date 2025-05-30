# Purpose
This Python code file is a comprehensive test suite designed to validate the functionality of task result persistence and task management within a distributed task execution framework. The file includes unit tests for two primary classes: `LocalDiskTaskResultPersistence` and `S3TaskResultPersistence`, which are responsible for saving and loading task results to and from local disk storage and Amazon S3, respectively. These tests ensure that task results can be serialized and deserialized correctly using JSON and Pickle formats, and they verify the behavior when attempting to load non-existent task results. The use of `pytest` fixtures and the `moto` library for mocking AWS services facilitates isolated and repeatable test scenarios.

Additionally, the file defines a `SleepTask` class, which simulates a task with a specified sleep duration, and a `TestTaskManager` class that tests the task dependency management and execution order using the `TaskManager` class. The `TestTaskManager` class includes asynchronous tests to verify that tasks are executed in the correct order based on their dependencies and that tasks can run concurrently when possible. It also checks the correct injection of IO results from completed dependencies into subsequent tasks. This test suite is crucial for ensuring the reliability and correctness of the task execution and persistence mechanisms in the broader system.
# Imports and Dependencies

---
- `asyncio`
- `time`
- `collections.abc`
- `pathlib`
- `tempfile`
- `boto3`
- `pytest`
- `moto`
- `utils.dag`
- `utils.task`


# Classes

---
### SleepTask 
- **Type**: `class`
- **Members**:
    - `sleep_time`: Stores the duration for which the task should sleep.
    - `captured_io_results`: Holds the IO results from dependencies for validation purposes.
- **Description**: The `SleepTask` class is a specialized type of `Task` that introduces a delay in its execution by sleeping for a specified amount of time. It is initialized with a task name, a sleep duration, and optional dependencies. The class overrides the `run_implementation` method to perform the sleep operation asynchronously and records the start and end times of the task execution. It also provides a `post_run_io` method to capture and store IO results from dependent tasks for further validation. This class is useful for simulating tasks that require a delay or for testing task dependencies and execution order.
- **Inherits From**:
    - Task

**Methods**

---
#### SleepTask.__init__
The `__init__` function initializes a `SleepTask` object with a task name, sleep time, and optional dependencies, setting up its node and capturing IO results.
- **Inputs**:
    - `task_name`: A string representing the name of the task.
    - `sleep_time`: A float indicating the amount of time the task should sleep during execution.
    - `dependencies`: An optional tuple of `Task` objects that this task depends on; defaults to an empty tuple if not provided.
- **Control Flow**:
    - The function checks if `dependencies` is provided; if not, it defaults to an empty tuple.
    - It calls the superclass `__init__` method with the task name, a new `LiteNode` object, and the dependencies.
    - The `LiteNode` is initialized with `NodeKind.FILE` and a path derived from the task name.
    - The `sleep_time` attribute is set to the provided `sleep_time` value.
    - The `captured_io_results` attribute is initialized to `None` to store IO results after task execution.
- **Output**:
    - The function does not return any value; it initializes the `SleepTask` object.


---
#### SleepTask.post_run_io
The `post_run_io` function captures and stores the dependent IO results for a task and returns a confirmation of IO completion.
- **Inputs**:
    - `task_result`: An instance of `TaskResult` representing the result of the task that has just been executed.
    - `dependent_io_results`: A dictionary mapping `Task` objects to their respective IO results, which are dictionaries with string keys and any type of values.
- **Control Flow**:
    - The function assigns the `dependent_io_results` to the `captured_io_results` attribute of the instance, allowing for later validation or inspection.
    - The function returns a dictionary indicating that IO operations have been completed.
- **Output**:
    - A dictionary with a single key-value pair `{"io_completed": True}` indicating that the IO operations have been successfully completed.


---
#### SleepTask.recoverable_errors
The `recoverable_errors` function returns an empty set of exception types, indicating no errors are considered recoverable.
- **Inputs**:
    - None
- **Control Flow**:
    - The function is defined as a method within a class, likely related to task execution or management.
    - It simply returns an empty set, indicating that no specific exceptions are marked as recoverable by this function.
- **Output**:
    - An empty set of type `set[type[Exception]]`, indicating no recoverable errors.


---
#### SleepTask.run_implementation
The `run_implementation` function asynchronously executes a task by sleeping for a specified duration and returns a `TaskResult` with the start and end times of the execution.
- **Inputs**:
    - `self`: Refers to the instance of the class `SleepTask` to which this method belongs.
    - `dependent_results`: A dictionary mapping `Task` objects to their corresponding `TaskResult` objects, representing the results of tasks that this task depends on.
- **Control Flow**:
    - Record the current time as `start_time`.
    - Pause execution asynchronously for the duration specified by `self.sleep_time`.
    - Record the current time as `end_time` after the sleep period.
    - Create and return a `TaskResult` object containing the `start_time` and `end_time`, serialized using the JSON method.
- **Output**:
    - A `TaskResult` object containing the start and end times of the task execution, serialized in JSON format.



---
### TestLocalDiskTaskResultPersistence 
- **Type**: `class`
- **Members**:
    - `temp_dir`: A pytest fixture that provides a temporary directory for testing.
    - `test_save_and_load_task_result_json`: Tests saving and loading a task result using JSON serialization.
    - `test_save_and_load_task_result_pickle`: Tests saving and loading a task result using Pickle serialization.
    - `test_load_nonexistent_task_result`: Tests loading a task result that does not exist, expecting None.
- **Description**: The `TestLocalDiskTaskResultPersistence` class is a test suite for verifying the functionality of the `LocalDiskTaskResultPersistence` class, which handles saving and loading task results to and from a local disk. It includes tests for saving and loading task results using both JSON and Pickle serialization methods, as well as a test for attempting to load a non-existent task result. The class uses a temporary directory fixture to ensure that tests do not affect the actual file system.

**Methods**

---
#### TestLocalDiskTaskResultPersistence.temp_dir
The `temp_dir` function is a fixture that provides a temporary directory path for use in tests.
- **Inputs**:
    - None
- **Control Flow**:
    - The function uses a `with` statement to create a `TemporaryDirectory`, ensuring that the directory is automatically cleaned up when the block is exited.
    - It yields a `Path` object pointing to the temporary directory, allowing the test to use this directory path.
- **Output**:
    - The function outputs a `Path` object representing the temporary directory.


---
#### TestLocalDiskTaskResultPersistence.test_load_nonexistent_task_result
The function `test_load_nonexistent_task_result` tests the behavior of loading a task result that does not exist in the local disk persistence system.
- **Inputs**:
    - `self`: An instance of the `TestLocalDiskTaskResultPersistence` class, which provides the context for the test.
    - `temp_dir`: A `Path` object representing a temporary directory used as the base directory for task result persistence.
- **Control Flow**:
    - Initialize a `LocalDiskTaskResultPersistence` object with `temp_dir` as the base directory.
    - Define `run_id` as 'test_run' and `task_id` as 'nonexistent_task'.
    - Attempt to load the task result using `persistence.load_task_result(run_id, task_id)`.
    - Assert that the result is `None`, indicating that no task result was found for the given `task_id`.
- **Output**:
    - The function does not return any value; it asserts that the result of loading a nonexistent task is `None`.


---
#### TestLocalDiskTaskResultPersistence.test_save_and_load_task_result_json
The function tests saving and loading a task result using JSON serialization with local disk persistence.
- **Inputs**:
    - `self`: An instance of the TestLocalDiskTaskResultPersistence class.
    - `temp_dir`: A temporary directory path used as the base directory for local disk persistence.
- **Control Flow**:
    - Initialize a LocalDiskTaskResultPersistence object with the provided temporary directory as the base directory.
    - Define a run ID and a task ID for the test.
    - Create a TaskResult object with data and specify JSON as the serialization method.
    - Save the task result using the persistence object's save_task_result method with the run ID, task ID, and result.
    - Load the task result using the persistence object's load_task_result method with the run ID and task ID.
    - Assert that the loaded result is not None and that its data matches the original result's data.
- **Output**:
    - The function does not return any value; it uses assertions to validate the test outcomes.


---
#### TestLocalDiskTaskResultPersistence.test_save_and_load_task_result_pickle
The function `test_save_and_load_task_result_pickle` tests the saving and loading of a task result using pickle serialization on a local disk.
- **Inputs**:
    - `self`: An instance of the `TestLocalDiskTaskResultPersistence` class, which provides the context for the test.
    - `temp_dir`: A temporary directory path provided by the pytest fixture, used as the base directory for storing task results.
- **Control Flow**:
    - Initialize a `LocalDiskTaskResultPersistence` object with `temp_dir` as the base directory.
    - Define `run_id` and `task_id` as identifiers for the task result.
    - Create a `TaskResult` object with data `{'key': 'value'}` and specify `SerializationMethod.PICKLE` for serialization.
    - Call `save_task_result` on the persistence object to save the task result using the specified `run_id` and `task_id`.
    - Call `load_task_result` on the persistence object to load the task result using the same `run_id` and `task_id`.
    - Assert that the loaded result is not `None`.
    - Assert that the data in the loaded result matches the original task result data.
- **Output**:
    - The function does not return any value; it uses assertions to verify that the task result is correctly saved and loaded.



---
### TestS3TaskResultPersistence 
- **Type**: `class`
- **Members**:
    - `s3_bucket`: A pytest fixture that sets up a mock S3 bucket for testing.
- **Description**: The `TestS3TaskResultPersistence` class is a test suite designed to verify the functionality of the `S3TaskResultPersistence` class, which handles saving and loading task results to and from an S3 bucket. It includes tests for saving and loading task results using both JSON and PICKLE serialization methods, as well as a test for attempting to load a non-existent task result. The class uses the `moto` library to mock AWS services, ensuring that tests do not interact with real AWS resources.

**Methods**

---
#### TestS3TaskResultPersistence.s3_bucket
The `s3_bucket` function is a pytest fixture that creates a mock S3 bucket using the `moto` library and yields its name for testing purposes.
- **Inputs**:
    - None
- **Control Flow**:
    - The function is decorated with `@pytest.fixture`, indicating it is a fixture for pytest tests.
    - The function uses the `mock_aws()` context manager from the `moto` library to mock AWS services.
    - Within the context manager, a boto3 S3 client is created.
    - A bucket named 'test-bucket' is created using the S3 client.
    - The function yields the name of the created bucket, 'test-bucket'.
- **Output**:
    - The function yields a string, which is the name of the created mock S3 bucket, 'test-bucket'.


---
#### TestS3TaskResultPersistence.test_load_nonexistent_task_result
The function `test_load_nonexistent_task_result` tests the behavior of loading a task result from an S3 bucket when the task does not exist.
- **Inputs**:
    - `self`: Represents the instance of the class `TestS3TaskResultPersistence` where this method is defined.
    - `s3_bucket`: A string representing the name of the S3 bucket used for testing.
- **Control Flow**:
    - An instance of `S3TaskResultPersistence` is created with the provided `s3_bucket` name.
    - A `run_id` and `task_id` are defined, with `task_id` set to a non-existent task.
    - The `load_task_result` method of the `S3TaskResultPersistence` instance is called with the `run_id` and `task_id`.
    - An assertion checks that the result of the `load_task_result` call is `None`, indicating that no result was found for the non-existent task.
- **Output**:
    - The function does not return any value, but it asserts that the result of loading a non-existent task is `None`.


---
#### TestS3TaskResultPersistence.test_save_and_load_task_result_json
The function `test_save_and_load_task_result_json` tests the saving and loading of a task result in JSON format using S3TaskResultPersistence.
- **Inputs**:
    - `self`: Represents the instance of the class `TestS3TaskResultPersistence` where this method is defined.
    - `s3_bucket`: A string representing the name of the S3 bucket used for storing and retrieving task results.
- **Control Flow**:
    - An instance of `S3TaskResultPersistence` is created with the provided S3 bucket name.
    - A `TaskResult` object is created with data `{"key": "value"}` and serialization method set to JSON.
    - The `save_task_result` method of the `S3TaskResultPersistence` instance is called to save the task result using the specified `run_id` and `task_id`.
    - The `load_task_result` method is called to retrieve the task result using the same `run_id` and `task_id`.
    - Assertions are made to ensure that the loaded result is not `None` and that its data matches the original result's data.
- **Output**:
    - The function does not return any value; it uses assertions to validate the correctness of the save and load operations.


---
#### TestS3TaskResultPersistence.test_save_and_load_task_result_pickle
The function tests the ability to save and load a task result using pickle serialization in an S3 bucket.
- **Inputs**:
    - `s3_bucket`: A string representing the name of the S3 bucket where the task result will be saved and loaded from.
- **Control Flow**:
    - An instance of S3TaskResultPersistence is created with the provided S3 bucket name.
    - A TaskResult object is created with data and PICKLE serialization method.
    - The task result is saved to the S3 bucket using the save_task_result method.
    - The task result is loaded from the S3 bucket using the load_task_result method.
    - Assertions are made to ensure the loaded result is not None and that its data matches the original result's data.
- **Output**:
    - The function does not return any value; it uses assertions to validate the test conditions.



---
### TestTaskManager 
- **Type**: `class`
- **Members**:
    - `setup_tasks`: A fixture that sets up a TaskManager with three SleepTask instances.
    - `test_task_dependency_basic`: An asynchronous test method that verifies task dependencies and execution order.
    - `test_post_run_io_injection`: An asynchronous test method that checks the post-run IO injection for task dependencies.
- **Description**: The `TestTaskManager` class is a test suite for verifying the functionality of a `TaskManager` and its handling of task dependencies and post-run IO operations. It includes fixtures and asynchronous test methods to ensure tasks are executed in the correct order, dependencies are respected, and IO results are correctly injected after task execution. The class uses the `pytest` framework and is designed to test the behavior of tasks managed by a `TaskManager`, particularly focusing on the execution timing and IO result handling of dependent tasks.

**Methods**

---
#### TestTaskManager.setup_tasks
The `setup_tasks` function initializes and returns a `TaskManager` along with three `SleepTask` instances, setting up a task execution environment with specified dependencies.
- **Inputs**:
    - None
- **Control Flow**:
    - Create a `SleepTask` instance named `task1` with a sleep time of 1 second and no dependencies.
    - Create a `SleepTask` instance named `task2` with a sleep time of 1.5 seconds, dependent on `task1`.
    - Create a `SleepTask` instance named `task3` with a sleep time of 1 second, also dependent on `task1`.
    - Store the three tasks in a list named `tasks`.
    - Instantiate a `TaskManager` with the `tasks` list, setting `serial_exe` to `False` and `persistence` to `None`.
    - Return the `TaskManager` instance along with the three task instances (`task1`, `task2`, `task3`).
- **Output**:
    - A tuple containing a `TaskManager` instance and three `SleepTask` instances (`task1`, `task2`, `task3`).


---
#### TestTaskManager.test_post_run_io_injection
The function `test_post_run_io_injection` verifies that the `post_run_io` method is called and correctly injects IO results from completed dependencies into tasks.
- **Inputs**:
    - `self`: Represents the instance of the class `TestTaskManager` to which this method belongs.
    - `setup_tasks`: A tuple containing a `TaskManager` instance and three `Task` instances (`task1`, `task2`, `task3`) set up for testing.
- **Control Flow**:
    - Unpack the `setup_tasks` tuple into `task_manager`, `task1`, `task2`, and `task3`.
    - Invoke `task_manager.run_tasks` with a `run_id` of 'test_run_io' to execute the tasks and trigger the `post_run_io` method.
    - Print the `captured_io_results` for each task to the console for debugging purposes.
    - Assert that `task1` has no `captured_io_results` since it has no dependencies.
    - Assert that `task2` and `task3` have `captured_io_results` indicating that `task1` has completed, verifying that `post_run_io` was called and results were injected correctly.
- **Output**:
    - The function does not return any value; it uses assertions to validate the expected behavior of the `post_run_io` method.


---
#### TestTaskManager.test_task_dependency_basic
The function `test_task_dependency_basic` tests the execution order and timing of tasks with dependencies using a `TaskManager`.
- **Inputs**:
    - `self`: The instance of the class `TestTaskManager` to which this method belongs.
    - `setup_tasks`: A tuple containing a `TaskManager` and three `Task` objects (`task1`, `task2`, `task3`) that are set up with specific dependencies and sleep times.
- **Control Flow**:
    - Unpack the `setup_tasks` tuple into `task_manager`, `task1`, `task2`, and `task3`.
    - Record the `global_start_time` using `time.time()`.
    - Run the tasks using `task_manager.run_tasks` with a `run_id` of 'test_run'.
    - Retrieve the start and completion times for each task from `task_manager.task_results`.
    - Assert that `task1` starts after `global_start_time` and completes at least 1 second after it starts.
    - Assert that `task2` starts after `task1` completes and completes at least 1.5 seconds after it starts.
    - Assert that `task3` starts after `task1` completes and completes at least 1 second after it starts.
    - Assert that `task3` starts concurrently with `task2` by checking the time difference is less than 0.1 seconds.
    - Print the start and completion times for each task.
    - Assert that both `task2` and `task3` complete at least 2 seconds after `global_start_time`.
- **Output**:
    - The function does not return any value; it performs assertions to validate task execution order and timing.



