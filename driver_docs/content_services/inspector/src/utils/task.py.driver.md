# Purpose
This Python code defines a framework for managing and executing tasks with dependencies, focusing on the serialization and persistence of task results. The code is structured around several key components: `TaskResult`, `TaskResultPersistence`, `LocalDiskTaskResultPersistence`, `S3TaskResultPersistence`, `Task`, and `TaskManager`. The `TaskResult` class encapsulates the result of a task, supporting serialization and deserialization using JSON or Pickle formats. The `TaskResultPersistence` abstract base class and its concrete implementations, `LocalDiskTaskResultPersistence` and `S3TaskResultPersistence`, provide mechanisms to save and load task results to and from local disk or Amazon S3, respectively. This allows for the persistence of task results across different runs, enabling resumption and recovery of task states.

The `Task` class represents an abstract task with dependencies, and it requires subclasses to implement specific task execution logic. The `TaskManager` class orchestrates the execution of tasks, handling dependencies, and managing the persistence of task results. It supports both serial and parallel execution of tasks using Python's `asyncio` library. The `TaskManager` also includes functionality to load previously persisted task results, which can be useful for resuming interrupted workflows. Overall, this code provides a robust framework for defining, executing, and managing tasks with complex dependencies, while ensuring that task results are efficiently serialized and persisted for future use.
# Imports and Dependencies

---
- `abc`
- `asyncio`
- `concurrent`
- `hashlib`
- `json`
- `pickle`
- `dataclasses`
- `enum`
- `pathlib`
- `typing`
- `uuid`
- `boto3`
- `botocore.exceptions`
- `utils.dag`


# Global Variables

---
### JSON 
- **Type**: `Enum`
- **Description**: The `JSON` variable is an enumeration member of the `SerializationMethod` Enum class. It represents the JSON serialization method, which is used to serialize data into a JSON string format. This method is chosen to maintain backward compatibility in case of Python version upgrades.
- **Use**: This variable is used to specify the JSON serialization method for data serialization and deserialization processes.


---
### PICKLE 
- **Type**: `str`
- **Description**: `PICKLE` is a member of the `SerializationMethod` enumeration, which is a subclass of `str` and `Enum`. It represents the string value 'pickle', indicating the use of Python's pickle module for serialization.
- **Use**: This variable is used to specify the serialization method as 'pickle' when serializing or deserializing data in the `TaskResult` class.


---
### TaskName 
- **Type**: `str`
- **Description**: `TaskName` is a global variable defined as a string type alias. It is used to represent the name of a task within the codebase. This alias provides a semantic meaning to the variable, indicating its purpose in the context of task management.
- **Use**: `TaskName` is used to denote the name of a task, providing clarity and context within the task management system.


---
### _extension_for_method 
- **Type**: `ClassVar[dict[SerializationMethod, str]]`
- **Description**: The `_extension_for_method` is a class variable defined within the `TaskResultPersistence` abstract base class. It is a dictionary that maps each `SerializationMethod` enum value to its corresponding file extension string. Specifically, it maps `SerializationMethod.JSON` to the string '.json' and `SerializationMethod.PICKLE` to the string '.pkl'. This mapping is used to determine the appropriate file extension for serialized task results based on the serialization method used.
- **Use**: This variable is used to determine the file extension for serialized task results based on the serialization method.


---
### _method_for_extension 
- **Type**: `dict[str, SerializationMethod]`
- **Description**: The `_method_for_extension` variable is a class variable within the `TaskResultPersistence` abstract base class. It is a dictionary that maps file extensions (as strings) to their corresponding `SerializationMethod` enumeration values. This mapping is the inverse of the `_extension_for_method` dictionary, which maps `SerializationMethod` values to file extensions.
- **Use**: This variable is used to determine the serialization method based on the file extension when loading task results.


---
### dependencies 
- **Type**: `tuple[type[Task], ...]`
- **Description**: The `dependencies` variable is a tuple that contains types of `Task` objects, representing the dependencies of a particular task. It is defined as a field in the `Task` class, which is an abstract base class for tasks in a task management system.
- **Use**: This variable is used to specify the tasks that must be completed before the current task can be executed.


---
### persistence 
- **Type**: `None | TaskResultPersistence`
- **Description**: The `persistence` variable is a global variable within the `TaskManager` class, which is either `None` or an instance of `TaskResultPersistence`. It is initialized by default to an instance of `S3TaskResultPersistence` with a specific bucket name, but can be configured differently when creating a `TaskManager` instance.
- **Use**: This variable is used to manage the persistence of task results, allowing them to be saved and loaded, typically to and from an S3 bucket.


---
### serial_exe 
- **Type**: `bool`
- **Description**: The `serial_exe` variable is a boolean flag within the `TaskManager` class that indicates whether tasks should be executed serially or concurrently. When set to `True`, tasks are executed one after another in a sequential manner. When set to `False`, tasks can be executed concurrently, allowing for parallel execution.
- **Use**: This variable is used to control the execution mode of tasks within the `TaskManager`, determining whether they run serially or concurrently.


---
### task_io_results 
- **Type**: `dict[type[Task], dict[str, any]]`
- **Description**: The `task_io_results` variable is a dictionary that maps each `Task` type to another dictionary containing string keys and any type of values. This structure is used to store the results of post-run I/O operations for each task.
- **Use**: This variable is used to store and retrieve the I/O results of tasks after they have been executed, allowing for further processing or analysis.


---
### task_results 
- **Type**: `dict[type[Task], TaskResult]`
- **Description**: The `task_results` variable is a dictionary that maps each `Task` type to its corresponding `TaskResult`. It is used to store the results of tasks after they have been executed, allowing for easy retrieval and management of task outcomes.
- **Use**: This variable is used to store and retrieve the results of tasks executed by the `TaskManager`.


---
### task_to_asynctask 
- **Type**: `dict[type[Task], asyncio.Task]`
- **Description**: The `task_to_asynctask` variable is a dictionary that maps each `Task` type to its corresponding `asyncio.Task` instance. This mapping allows the `TaskManager` to keep track of the asynchronous tasks that are scheduled and running for each `Task` type.
- **Use**: This variable is used to store and retrieve the `asyncio.Task` instances associated with each `Task` type, enabling the management and execution of tasks asynchronously.


---
### tasks 
- **Type**: `list[type[Task]]`
- **Description**: The `tasks` variable is a list that holds instances of the `Task` class or its subclasses. Each `Task` represents a unit of work that can be executed, potentially with dependencies on other tasks.
- **Use**: This variable is used to manage and execute a collection of tasks within the `TaskManager` class, allowing for both serial and parallel execution of tasks.


---
### write_executor 
- **Type**: `ThreadPoolExecutor`
- **Description**: The `write_executor` is a `ThreadPoolExecutor` instance initialized with a maximum of 5 worker threads. It is used to handle blocking I/O operations in a non-blocking manner by offloading them to a separate thread pool.
- **Use**: This variable is used to execute the `save_task_result` method of the `persistence` object in a separate thread, allowing asynchronous tasks to continue without being blocked by I/O operations.


---
### write_queue 
- **Type**: `asyncio.Queue`
- **Description**: The `write_queue` is an instance of `asyncio.Queue` used within the `TaskManager` class. It is designed to hold task results that need to be written to persistent storage, such as S3, in an asynchronous manner. This queue facilitates the decoupling of task execution from the persistence layer, allowing task results to be enqueued for writing without blocking the main execution flow.
- **Use**: This variable is used to queue task results for asynchronous writing to persistent storage, ensuring non-blocking task execution.


# Classes

---
### LocalDiskTaskResultPersistence 
- **Type**: `class`
- **Members**:
    - `base_dir`: The base directory path where task results are stored.
- **Description**: The `LocalDiskTaskResultPersistence` class is responsible for persisting task results to the local disk. It inherits from `TaskResultPersistence` and implements methods to save and load task results using either JSON or PICKLE serialization methods. The class ensures that the necessary directories are created and handles the serialization and deserialization of task results based on the specified method. It provides a local storage solution for task results, making it suitable for environments where local disk access is available and preferred over remote storage solutions.
- **Inherits From**:
    - TaskResultPersistence

**Methods**

---
#### LocalDiskTaskResultPersistence.__init__
The `__init__` function initializes a `LocalDiskTaskResultPersistence` object by setting up a base directory for storing task results on the local disk.
- **Inputs**:
    - `base_dir`: A `Path` object representing the base directory where task results will be stored.
- **Control Flow**:
    - The function takes a `base_dir` argument and converts it to a `Path` object, ensuring it is a valid path.
    - It then creates the directory specified by `base_dir`, including any necessary parent directories, and does not raise an error if the directory already exists.
- **Output**:
    - The function does not return any value; it initializes the object's state by setting up the base directory.


---
#### LocalDiskTaskResultPersistence._get_file_base_path
The function `_get_file_base_path` constructs a file path based on a base directory, run ID, and task ID.
- **Inputs**:
    - `run_id`: A string representing the unique identifier for a specific run.
    - `task_id`: A string representing the unique identifier for a specific task.
- **Control Flow**:
    - The function takes two string inputs, `run_id` and `task_id`.
    - It constructs a file path by combining the base directory (`self.base_dir`), `run_id`, and `task_id` using the `/` operator, which is overloaded by the `Path` class to concatenate paths.
- **Output**:
    - The function returns a `Path` object representing the constructed file path.


---
#### LocalDiskTaskResultPersistence._get_run_dir
The `_get_run_dir` function constructs and returns a directory path for a specific run using a base directory and a given run ID.
- **Inputs**:
    - `run_id`: A string representing the unique identifier for a specific run, used to create a subdirectory within the base directory.
- **Control Flow**:
    - The function takes a single input, `run_id`, which is a string.
    - It accesses the `base_dir` attribute of the class instance, which is a `Path` object representing the base directory.
    - It constructs a new `Path` object by appending the `run_id` to the `base_dir` using the `/` operator, which is overloaded in the `Path` class to concatenate paths.
- **Output**:
    - The function returns a `Path` object representing the directory path for the specified run ID within the base directory.


---
#### LocalDiskTaskResultPersistence.load_task_result
The `load_task_result` function attempts to load a task result from the local disk using a specified run ID and task ID, returning the deserialized result if found, or None if not.
- **Inputs**:
    - `run_id`: A string representing the unique identifier for the run, used to locate the task result file.
    - `task_id`: A string representing the unique identifier for the task, used to locate the task result file.
- **Control Flow**:
    - The function first constructs a base file path using the provided run ID and task ID by calling the `_get_file_base_path` method.
    - It iterates over the available serialization methods and their corresponding file extensions defined in `_extension_for_method`.
    - For each serialization method, it constructs a file path by appending the appropriate extension to the base path.
    - It checks if the file exists at the constructed path; if it does, it reads the file content as text for JSON or bytes for other formats.
    - The function then deserializes the data using the `TaskResult.deserialize` method with the detected serialization method and returns the deserialized `TaskResult`.
    - If no file is found for any serialization method, the function returns None.
- **Output**:
    - The function returns a `TaskResult` object if a corresponding file is found and successfully deserialized, otherwise it returns None.


---
#### LocalDiskTaskResultPersistence.save_task_result
The `save_task_result` function saves the result of a task to a local disk, using either JSON or PICKLE serialization, based on the specified method.
- **Inputs**:
    - `run_id`: A string representing the unique identifier for the run.
    - `task_id`: A string representing the unique identifier for the task.
    - `result`: An instance of `TaskResult` containing the data to be saved and the serialization method to be used.
- **Control Flow**:
    - Retrieve the directory path for the given run ID using `_get_run_dir` and create it if it doesn't exist.
    - Determine the base file path for the task using `_get_file_base_path`.
    - Select the appropriate file extension based on the serialization method of the result.
    - Serialize the task result data using the `serialize` method of `TaskResult`.
    - If the serialization method is JSON, write the serialized data as text to the file.
    - If the serialization method is PICKLE, write the serialized data as bytes to the file.
    - Raise a `ValueError` if the serialization method is neither JSON nor PICKLE.
- **Output**:
    - The function does not return any value; it performs file operations to save the task result to disk.



---
### S3TaskResultPersistence 
- **Type**: `class`
- **Members**:
    - `s3_client`: An instance of the boto3 S3 client used to interact with AWS S3.
    - `bucket_name`: The name of the S3 bucket where task results are stored.
- **Description**: The `S3TaskResultPersistence` class is responsible for persisting task results to an AWS S3 bucket. It inherits from the `TaskResultPersistence` abstract base class and implements methods to save and load task results using S3 as the storage backend. The class uses the boto3 library to interact with S3, and it supports different serialization methods for task results, such as JSON and PICKLE. The class handles exceptions related to missing AWS credentials and missing S3 keys, ensuring robust interaction with the S3 service.
- **Inherits From**:
    - TaskResultPersistence

**Methods**

---
#### S3TaskResultPersistence.__init__
The `__init__` function initializes an instance of the `S3TaskResultPersistence` class by setting up an S3 client and storing the provided bucket name.
- **Inputs**:
    - `bucket_name`: A string representing the name of the S3 bucket to be used for storing task results.
- **Control Flow**:
    - The function is a constructor and is called when an instance of the `S3TaskResultPersistence` class is created.
    - It initializes an S3 client using the `boto3.client` method with 's3' as the service name.
    - It assigns the provided `bucket_name` to the instance variable `self.bucket_name`.
- **Output**:
    - The function does not return any value; it initializes the instance variables `s3_client` and `bucket_name`.


---
#### S3TaskResultPersistence.load_task_result
The `load_task_result` function attempts to retrieve and deserialize a task result from an S3 bucket using a specified run and task ID.
- **Inputs**:
    - `run_id`: A string representing the unique identifier for the run, used as part of the S3 object key.
    - `task_id`: A string representing the unique identifier for the task, used as part of the S3 object key.
- **Control Flow**:
    - Constructs a base object key using the provided `run_id` and `task_id`.
    - Iterates over available serialization methods and their corresponding file extensions.
    - For each method, constructs the full object key by appending the extension to the base object key.
    - Attempts to retrieve the object from the S3 bucket using the constructed object key.
    - Handles exceptions for missing keys, missing AWS credentials, and other errors, printing an error message and returning `None` if an error occurs.
    - Reads the body of the retrieved object and deserializes it using the appropriate method based on the serialization method.
    - Returns the deserialized `TaskResult` if successful, otherwise continues to the next serialization method.
    - Returns `None` if no valid object is found for any serialization method.
- **Output**:
    - Returns a `TaskResult` object if a valid serialized object is found and successfully deserialized, otherwise returns `None`.


---
#### S3TaskResultPersistence.save_task_result
The `save_task_result` function stores a serialized task result in an S3 bucket using a specific object key format.
- **Inputs**:
    - `run_id`: A string representing the unique identifier for the run, used as part of the S3 object key.
    - `task_id`: A string representing the unique identifier for the task, used as part of the S3 object key.
    - `result`: An instance of `TaskResult` containing the data to be serialized and stored, along with the serialization method.
- **Control Flow**:
    - Constructs a base object key using the `run_id` and `task_id`.
    - Determines the file extension based on the serialization method of the `result`.
    - Combines the base object key and the extension to form the complete S3 object key.
    - Serializes the `result` data using its `serialize` method.
    - Uses the S3 client to put the serialized data into the specified S3 bucket with the constructed object key.
- **Output**:
    - The function does not return any value; it performs an action of storing the serialized task result in an S3 bucket.



---
### SerializationMethod 
- **Type**: `class`
- **Members**:
    - `JSON`: Represents the JSON serialization method.
    - `PICKLE`: Represents the Pickle serialization method.
- **Description**: The `SerializationMethod` class is an enumeration that defines two serialization methods: JSON and PICKLE. It inherits from both `str` and `Enum`, allowing it to be used as a string while also providing enumeration capabilities. The JSON method is preferred for maintaining backward compatibility with potential Python version upgrades, while the PICKLE method should be used sparingly due to concerns about compatibility with future Python versions.
- **Inherits From**:
    - str
    - Enum


---
### Task 
- **Type**: `dataclass`
- **Members**:
    - `task_name`: The name of the task.
    - `node`: The LiteNode associated with the task.
    - `dependencies`: A tuple of Task types that this task depends on.
- **Description**: The `Task` class is an abstract base class representing a unit of work that can be executed asynchronously. It is designed to be part of a dependency graph where each task can have dependencies on other tasks. The class requires subclasses to implement the `run_implementation` and `post_run_io` methods, which define the core logic of the task and any post-execution input/output operations, respectively. The class also provides properties for generating a stable identifier and a hashed version of it, which are used for task identification and comparison. The `run` method orchestrates the execution of the task, ensuring that all dependencies are resolved before the task itself is executed.
- **Inherits From**:
    - abc.ABC

**Methods**

---
#### Task.__eq__
The `__eq__` function checks if two `Task` objects are equal by comparing their hash values.
- **Inputs**:
    - `self`: The current instance of the `Task` class.
    - `other`: Another instance of the `Task` class to compare against.
- **Control Flow**:
    - Check if the `other` object is an instance of the `Task` class.
    - If `other` is a `Task`, compare the hash of `self` with the hash of `other`.
    - Return `True` if the hashes are equal, otherwise return `False`.
    - If `other` is not a `Task`, return `False`.
- **Output**:
    - A boolean value indicating whether the two `Task` objects are considered equal.


---
#### Task.__hash__
The `__hash__` function returns the hash value of the `stable_id` property of a `Task` object.
- **Inputs**:
    - None
- **Control Flow**:
    - The function directly returns the hash value of the `stable_id` property of the object it is called on.
- **Output**:
    - An integer representing the hash value of the `stable_id` property of the `Task` object.


---
#### Task.__str__
The `__str__` method returns a string representation of a `Task` object, including its class name, node's root relative path, and node status.
- **Inputs**:
    - `self`: An instance of the `Task` class.
- **Control Flow**:
    - The method constructs a formatted string using the class name of the instance (`self.__class__.__name__`).
    - It accesses the `node` attribute of the instance to retrieve `root_rel_path` and `status` properties.
    - The method returns the constructed string.
- **Output**:
    - A string that describes the `Task` instance, including its class name, node's root relative path, and node status.


---
#### Task.hashed_stable_id
The `hashed_stable_id` function returns a SHA-256 hash of the stable identifier for a task.
- **Inputs**:
    - None
- **Control Flow**:
    - The function retrieves the `stable_id` property of the object it is called on.
    - It encodes this `stable_id` string into bytes.
    - It computes the SHA-256 hash of the encoded bytes using the `hashlib.sha256` function.
    - It converts the resulting hash object to a hexadecimal string using the `hexdigest` method.
    - The function returns this hexadecimal string.
- **Output**:
    - A hexadecimal string representing the SHA-256 hash of the stable identifier.


---
#### Task.post_run_io
The `post_run_io` function is an abstract method intended to handle post-execution input/output operations for a task, using the task's result and the results of its dependencies.
- **Inputs**:
    - `task_result`: An instance of `TaskResult` representing the result of the task that has just been executed.
    - `dependent_io_results`: A dictionary mapping each dependent `Task` to a dictionary of input/output results, where the keys are strings and the values can be of any type.
- **Control Flow**:
    - The function is defined as an abstract method, meaning it must be implemented by any subclass of the `Task` class.
    - The function is asynchronous, indicating it will perform operations that may involve waiting, such as I/O operations.
    - The function currently raises a `NotImplementedError`, serving as a placeholder to enforce implementation in subclasses.
- **Output**:
    - The function is expected to return a dictionary with string keys and values of any type, representing the results of the post-execution I/O operations.


---
#### Task.run
The `run` function asynchronously executes a task by invoking its `run_implementation` method with the results of its dependent tasks.
- **Inputs**:
    - `dependent_results`: A dictionary mapping `Task` objects to their corresponding `TaskResult` objects, representing the results of tasks that the current task depends on.
- **Control Flow**:
    - The function is defined as asynchronous, indicating it will perform non-blocking operations.
    - It directly calls and awaits the `run_implementation` method of the task, passing the `dependent_results` as an argument.
    - The function returns the result of the awaited `run_implementation` call.
- **Output**:
    - The function returns a `TaskResult` object, which is the result of executing the task's `run_implementation` method.


---
#### Task.run_implementation
The `run_implementation` function is an abstract method intended to be overridden by subclasses to execute a task using the results of its dependencies.
- **Inputs**:
    - `self`: Refers to the instance of the class where this method is implemented.
    - `dependent_results`: A dictionary mapping `Task` objects to their corresponding `TaskResult` objects, representing the results of tasks that the current task depends on.
- **Control Flow**:
    - The function is defined as an asynchronous method, indicated by the `async` keyword, meaning it is intended to be run with an event loop and can use `await` to pause execution until awaited tasks are complete.
    - The function raises a `NotImplementedError`, indicating that it is an abstract method and must be implemented by subclasses of the class in which it is defined.
- **Output**:
    - The function does not return any value as it raises a `NotImplementedError`, but when implemented, it is expected to return a `TaskResult` object.


---
#### Task.stable_id
The `stable_id` function generates a unique identifier string for a task based on its class name, node stable ID, and the stable IDs of its dependencies.
- **Inputs**:
    - None
- **Control Flow**:
    - Initialize `id_str` with the class name and node stable ID of the task.
    - Check if the task has dependencies.
    - If dependencies exist, concatenate their stable IDs to form `dep_str`.
    - Append `dep_str` to `id_str` if dependencies are present.
    - Return the final `id_str` as the stable identifier.
- **Output**:
    - A string representing the stable identifier for the task, incorporating its class name, node stable ID, and any dependencies' stable IDs.



---
### TaskManager 
- **Type**: `dataclass`
- **Members**:
    - `tasks`: A list of Task types to be managed and executed.
    - `serial_exe`: A boolean indicating if tasks should be executed serially.
    - `task_results`: A dictionary mapping Task types to their TaskResult.
    - `task_io_results`: A dictionary mapping Task types to their IO results.
    - `task_to_asynctask`: A dictionary mapping Task types to asyncio.Task objects.
    - `persistence`: An optional TaskResultPersistence object for saving task results.
    - `write_queue`: An asyncio.Queue for managing task result writing.
    - `write_executor`: A ThreadPoolExecutor for executing write operations.
- **Description**: The TaskManager class is responsible for managing and executing a collection of tasks, handling their dependencies, and persisting their results. It supports both serial and parallel execution of tasks, and can load previously persisted task results to resume operations. The class also provides a method to configure S3-based persistence for task results. It uses asyncio for asynchronous task scheduling and execution, and a thread pool for handling IO operations related to task result persistence.

**Methods**

---
#### TaskManager._can_skip_task
The `_can_skip_task` function checks if a task's result is already available, indicating that the task can be skipped.
- **Inputs**:
    - `task`: A class type of `Task` for which the function checks if the task result is already present in the `task_results` dictionary.
- **Control Flow**:
    - Retrieve the task result from the `task_results` dictionary using the provided `task` as the key.
    - Check if the retrieved task result is not `None`.
- **Output**:
    - Returns `True` if the task result is not `None`, indicating the task can be skipped; otherwise, returns `False`.


---
#### TaskManager._run_task
The `_run_task` function executes a given task, ensuring all its dependencies are completed first, and handles task result storage and post-run I/O operations.
- **Inputs**:
    - `task`: A `Task` object representing the task to be executed, which includes its dependencies and execution logic.
- **Control Flow**:
    - Check if tasks should be executed serially or concurrently based on `self.serial_exe` flag.
    - If serial execution is enabled, await each dependency task sequentially using `_schedule_and_await_task`.
    - If concurrent execution is enabled, gather all dependency tasks and await them concurrently using `asyncio.gather`.
    - Check if the task can be skipped using `_can_skip_task`; if so, retrieve the result from `self.task_results`.
    - If the task cannot be skipped, execute the task's `run` method with results of its dependencies and store the result in `self.task_results`.
    - Execute the task's `post_run_io` method unconditionally, storing the I/O result in `self.task_io_results`.
    - Put the task's hashed stable ID and result into `self.write_queue` for further processing.
    - Return the task result.
- **Output**:
    - Returns a `TaskResult` object representing the outcome of the executed task.


---
#### TaskManager._schedule_and_await_task
The `_schedule_and_await_task` function schedules a given task and awaits its completion asynchronously.
- **Inputs**:
    - `task`: A class type of `Task` that represents the task to be scheduled and awaited.
- **Control Flow**:
    - The function calls `_schedule_task` with the provided `task` to schedule it and obtain an `asyncio.Task`.
    - It then awaits the completion of the scheduled `asyncio.Task` using the `await` keyword.
- **Output**:
    - The function returns the result of the awaited `asyncio.Task`, which is the completion of the scheduled task.


---
#### TaskManager._schedule_task
The `_schedule_task` function schedules a given task by creating an asyncio task if it hasn't been scheduled yet and returns the asyncio task associated with it.
- **Inputs**:
    - `task`: A class type of `Task` that needs to be scheduled.
- **Control Flow**:
    - Check if the task is not already in the `task_to_asynctask` dictionary.
    - If not, create a coroutine for the task using `_run_task(task)`.
    - Create an asyncio task from the coroutine using `asyncio.create_task()` and store it in `task_to_asynctask` with the task as the key.
    - Return the asyncio task associated with the given task from `task_to_asynctask`.
- **Output**:
    - Returns an `asyncio.Task` object associated with the given task.


---
#### TaskManager._write_task_results
The `_write_task_results` function asynchronously writes task results to a persistence layer using a queue and an executor.
- **Inputs**:
    - `run_id`: A string representing the unique identifier for the current run of tasks.
- **Control Flow**:
    - The function enters an infinite loop to continuously process items from the `write_queue`.
    - It awaits an item from the `write_queue` using `await self.write_queue.get()`.
    - If the item is `None`, the loop breaks, indicating that there are no more results to process.
    - For each item, it unpacks the `task_id` and `result`.
    - It uses `asyncio.get_running_loop().run_in_executor` to run the `save_task_result` method of the `persistence` object in a separate thread, passing `run_id`, `task_id`, and `result` as arguments.
    - Once the loop exits, it prints 'Writer task done' to indicate completion.
- **Output**:
    - The function does not return any value; it performs side effects by writing task results to a persistence layer.


---
#### TaskManager.load_persisted_results
The `load_persisted_results` function loads previously saved task results from a persistence layer based on a given configuration of run IDs and node statuses.
- **Inputs**:
    - `self`: An instance of the class containing the function, typically a TaskManager.
    - `result_loading_config`: A list of tuples, where each tuple contains a run ID (string) and a set of NodeStatus values, specifying which task results to load.
- **Control Flow**:
    - Initialize a dictionary `task_by_id` mapping task hashed stable IDs to Task objects from `self.tasks`.
    - Print a message indicating the start of loading persisted results.
    - Initialize an empty dictionary `loaded_results` to store the loaded task results.
    - Iterate over each tuple in `result_loading_config`, extracting `run_id` and `node_statuses`.
    - For each tuple, create a list `needed` of task IDs whose node status is in `node_statuses`.
    - Use a `ThreadPoolExecutor` with a maximum of 25 workers to submit tasks for loading results from persistence for each task ID in `needed`.
    - Map each future to its corresponding task ID in `future_map`.
    - As each future completes, retrieve the result and update `loaded_results` if the result is valid and the task ID exists in `task_by_id`.
    - Handle exceptions during result loading by printing an error message.
    - Update `self.task_results` with the loaded results.
    - Print a message indicating the number of successfully loaded task results.
- **Output**:
    - The function does not return any value; it updates the `self.task_results` dictionary with the loaded task results.


---
#### TaskManager.run_tasks
The `run_tasks` function executes a series of tasks asynchronously, optionally loading persisted results and writing task results to a persistence layer.
- **Inputs**:
    - `run_id`: A UUID representing the unique identifier for the current run of tasks.
    - `result_loading_config`: An optional list of tuples, each containing a UUID and a set of NodeStatus, used to load persisted task results before execution.
- **Control Flow**:
    - Initialize `result_loading_config` to an empty list if not provided.
    - If `result_loading_config` is not empty and persistence is enabled, load persisted results using `load_persisted_results`.
    - If persistence is enabled, create an asynchronous task to write task results using `_write_task_results`.
    - Check if tasks should be executed serially or concurrently based on `serial_exe`.
    - If `serial_exe` is True, iterate over tasks and await each task's execution using `_schedule_and_await_task`.
    - If `serial_exe` is False, use `asyncio.gather` to execute all tasks concurrently.
    - In the `finally` block, put `None` in the `write_queue` to signal the writer task to stop, and await the writer task if persistence is enabled.
    - Return the `task_results` dictionary containing the results of all executed tasks.
- **Output**:
    - A dictionary mapping each Task type to its corresponding TaskResult, representing the results of the executed tasks.


---
#### TaskManager.with_s3_persistence
The `with_s3_persistence` function creates a `TaskManager` instance with S3-based task result persistence using a specified S3 bucket.
- **Inputs**:
    - `cls`: The class type, expected to be `TaskManager`, used to create an instance.
    - `bucket_name`: A string representing the name of the S3 bucket where task results will be persisted.
    - `*args`: Additional positional arguments to be passed to the `TaskManager` constructor.
    - `**kwargs`: Additional keyword arguments to be passed to the `TaskManager` constructor.
- **Control Flow**:
    - The function is a class method of `TaskManager` and is called with the class itself as the first argument (`cls`).
    - It initializes an instance of `S3TaskResultPersistence` with the provided `bucket_name`.
    - The function returns a new instance of `TaskManager`, passing any additional arguments and setting the `persistence` attribute to the `S3TaskResultPersistence` instance.
- **Output**:
    - Returns an instance of `TaskManager` with S3 persistence configured.



---
### TaskResult 
- **Type**: `dataclass`
- **Members**:
    - `data`: Holds the data associated with the task result.
    - `serialization`: Specifies the method used for serializing the data.
- **Description**: The `TaskResult` class is a data structure that encapsulates the result of a task, including the data and the method of serialization used. It provides methods to serialize the data into either JSON or PICKLE formats and to deserialize data back into a `TaskResult` object. This class is designed to facilitate the storage and retrieval of task results in a serialized form, ensuring compatibility with different serialization methods.

**Methods**

---
#### TaskResult.deserialize
The `deserialize` function converts serialized data back into a `TaskResult` object using the specified serialization method.
- **Inputs**:
    - `cls`: The class reference, typically `TaskResult`, used to create a new instance.
    - `data`: The serialized data, which can be either a string (for JSON) or bytes (for PICKLE).
    - `method`: The serialization method used, which is an instance of the `SerializationMethod` enum, either `JSON` or `PICKLE`.
- **Control Flow**:
    - Check if the method is `SerializationMethod.JSON` and the data is a string; if so, deserialize using `json.loads`.
    - Check if the method is `SerializationMethod.PICKLE` and the data is bytes; if so, deserialize using `pickle.loads`.
    - If neither condition is met, raise a `ValueError` indicating an invalid data type for the given serialization method.
    - Return a new instance of `TaskResult` with the deserialized data and the serialization method.
- **Output**:
    - A `TaskResult` object containing the deserialized data and the serialization method used.


---
#### TaskResult.serialize
The `serialize` function converts the `data` attribute of a `TaskResult` instance into a serialized format (either JSON or PICKLE) based on the specified `serialization` method.
- **Inputs**:
    - None
- **Control Flow**:
    - Check if the `serialization` attribute is `SerializationMethod.JSON` and if so, serialize `data` using `json.dumps()` and return the result as a string.
    - Check if the `serialization` attribute is `SerializationMethod.PICKLE` and if so, serialize `data` using `pickle.dumps()` and return the result as bytes.
    - If the `serialization` method is neither JSON nor PICKLE, raise a `ValueError` indicating an unsupported serialization method.
- **Output**:
    - The function returns the serialized data as a string if using JSON, or as bytes if using PICKLE.



---
### TaskResultPersistence 
- **Type**: `class`
- **Members**:
    - `_extension_for_method`: A class variable mapping serialization methods to their respective file extensions.
    - `_method_for_extension`: A class variable mapping file extensions to their respective serialization methods.
- **Description**: The `TaskResultPersistence` class is an abstract base class that defines the interface for persisting task results. It includes abstract methods `save_task_result` and `load_task_result` which must be implemented by subclasses to handle the saving and loading of `TaskResult` objects, respectively. The class also provides mappings between serialization methods and file extensions to facilitate the persistence process.
- **Inherits From**:
    - ABC

**Methods**

---
#### TaskResultPersistence.load_task_result
The `load_task_result` function retrieves a previously saved task result based on a given run ID and task ID, returning either the deserialized result or None if not found.
- **Inputs**:
    - `run_id`: A string representing the unique identifier for a specific run of tasks.
    - `task_id`: A string representing the unique identifier for a specific task within the run.
- **Control Flow**:
    - The function constructs a base path or object key using the provided `run_id` and `task_id`.
    - It iterates over possible serialization methods (JSON and PICKLE) to determine the file extension or object key suffix.
    - For each serialization method, it checks if the corresponding file or object exists.
    - If a file or object is found, it reads the data and deserializes it using the appropriate method.
    - If deserialization is successful, it returns the `TaskResult` object.
    - If no file or object is found for any serialization method, it returns None.
- **Output**:
    - The function returns a `TaskResult` object if a saved result is found and successfully deserialized, otherwise it returns None.


---
#### TaskResultPersistence.save_task_result
The `save_task_result` function stores the result of a task identified by a run ID and task ID using a specified serialization method.
- **Inputs**:
    - `run_id`: A string representing the unique identifier for the run to which the task belongs.
    - `task_id`: A string representing the unique identifier for the task whose result is being saved.
    - `result`: An instance of `TaskResult` containing the data to be saved and the serialization method to be used.
- **Control Flow**:
    - The function first determines the directory path for the run using the `run_id` and creates it if it doesn't exist.
    - It then constructs the file path for the task result using the `task_id` and the appropriate file extension based on the serialization method.
    - The task result is serialized using the specified method (JSON or PICKLE).
    - The serialized data is written to a file at the constructed path, using either text or binary mode depending on the serialization method.
- **Output**:
    - The function does not return any value; it performs the side effect of saving the task result to a file.



# Functions

---
### _flatten 
The `_flatten` function recursively flattens a task and its dependencies into a list, avoiding duplicates by tracking seen tasks.
- **Inputs**:
    - `task`: A `Task` type object representing the task to be flattened.
    - `seen`: A set of `Task` type objects that have already been processed to avoid duplication.
- **Control Flow**:
    - Check if the task is already in the `seen` set; if so, return an empty list to avoid processing it again.
    - Add the current task to the `seen` set to mark it as processed.
    - Return a list containing the current task followed by the flattened list of all its dependencies, recursively calling `_flatten` on each dependency.
- **Output**:
    - A list of `Task` type objects representing the flattened task and its dependencies, with no duplicates.


---
### flatten_tasks 
The `flatten_tasks` function recursively flattens a list of tasks and their dependencies into a single list without duplicates.
- **Inputs**:
    - `tasks`: A list of Task types, where each Task may have dependencies on other Tasks.
- **Control Flow**:
    - Define a nested helper function `_flatten` that takes a task and a set of seen tasks.
    - Check if the current task is already in the seen set; if so, return an empty list to avoid duplicates.
    - Add the current task to the seen set to mark it as processed.
    - Return a list containing the current task followed by the flattened list of all its dependencies, recursively processed by `_flatten`.
    - Initialize an empty set `seen` to keep track of processed tasks.
    - Return a flattened list of all tasks and their dependencies by applying `_flatten` to each task in the input list.
- **Output**:
    - A list of Task types, representing the input tasks and all their dependencies, flattened into a single list without duplicates.


