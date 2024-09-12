import abc
import asyncio
import hashlib
import json
import pickle
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import boto3
import modal.exception
from botocore.exceptions import NoCredentialsError

TaskName = str


class TaskResultKind(Enum):
    SUCCESS = "success"
    RECOVERABLE_ERROR = "recoverable_error"
    UNRECOVERABLE_ERROR = "unrecoverable_error"


@dataclass
class TaskResult:
    result: dict[str, any]
    state: TaskResultKind

    def to_json(self) -> str:
        return json.dumps({"result": self.result, "state": self.state.value})

    @classmethod
    def from_json(cls, json_str: str) -> "TaskResult":
        data = json.loads(json_str)
        return TaskResult(result=data["result"], state=TaskResultKind(data["state"]))


# TODO check exception handling and propagation is correct!
# If a task fails, the dependent tasks should not run, but we can still run other tasks if desired.


class TaskResultPersistence(ABC):
    @abstractmethod
    def save_task_result(self, run_id: str, task_id: str, result: TaskResult) -> None:
        pass

    @abstractmethod
    def load_task_result(self, run_id: str, task_id: str) -> None | TaskResult:
        pass

    @abstractmethod
    def load_all_results(self, run_id: str) -> dict[str, TaskResult]:
        pass

    @abstractmethod
    def clear_all_results(self, run_id: str) -> None:
        pass


class LocalDiskTaskResultPersistence(TaskResultPersistence):
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, run_id: str, task_id: str) -> Path:
        return self.base_dir / run_id / f"{task_id}.json"

    def _get_run_dir(self, run_id: str) -> Path:
        return self.base_dir / run_id

    def save_task_result(self, run_id: str, task_id: str, result: TaskResult) -> None:
        run_dir = self._get_run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        file_path = self._get_file_path(run_id, task_id)
        with file_path.open("w") as f:
            f.write(result.to_json())

    def load_task_result(self, run_id: str, task_id: str) -> None | TaskResult:
        file_path = self._get_file_path(run_id, task_id)
        if not file_path.exists():
            return None
        with file_path.open("r") as f:
            json_str = f.read()
        return TaskResult.from_json(json_str)

    def load_all_results(self, run_id: str) -> dict[str, TaskResult]:
        results = {}
        run_dir = self._get_run_dir(run_id)
        if not run_dir.exists():
            return results
        for file_path in run_dir.glob("*.json"):
            task_id = file_path.stem
            result = self.load_task_result(run_id, task_id)
            if result:
                results[task_id] = result
        return results

    def clear_all_results(self, run_id: str) -> None:
        run_dir = self._get_run_dir(run_id)
        if not run_dir.exists():
            return
        for file_path in run_dir.glob("*.json"):
            file_path.unlink()
        run_dir.rmdir()


class S3TaskResultPersistence(TaskResultPersistence):
    def __init__(self, bucket_name: str):
        self.s3_client = boto3.client("s3")
        self.bucket_name = bucket_name

    def save_task_result(self, run_id: str, task_id: str, result: TaskResult) -> None:
        object_key = f"{run_id}/{task_id}.json"
        self.s3_client.put_object(
            Bucket=self.bucket_name, Key=object_key, Body=result.to_json()
        )

    def load_task_result(self, run_id: str, task_id: str) -> None | TaskResult:
        object_key = f"{run_id}/{task_id}.json"
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=object_key
            )
            result = TaskResult.from_json(response["Body"].read().decode("utf-8"))
            return result
        except self.s3_client.exceptions.NoSuchKey:
            return None
        except NoCredentialsError:
            raise Exception("AWS credentials not found.")
        except Exception as e:
            print(f"Error fetching data from S3: {e}")
            return None

    def load_all_results(self, run_id: str) -> dict[str, TaskResult]:
        results = {}
        paginator = self.s3_client.get_paginator("list_objects_v2")
        prefix = f"{run_id}/"
        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
            for obj in page.get("Contents", []):
                task_id = obj["Key"].split("/")[-1].replace(".json", "")
                result = self.load_task_result(run_id, task_id)
                if result:
                    results[task_id] = result
        return results

    def clear_all_results(self, run_id: str) -> None:
        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            prefix = f"{run_id}/"
            delete_us = {"Objects": []}
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                for obj in page.get("Contents", []):
                    delete_us["Objects"].append({"Key": obj["Key"]})
            if delete_us["Objects"]:
                self.s3_client.delete_objects(Bucket=self.bucket_name, Delete=delete_us)
        except NoCredentialsError as e:
            raise Exception("AWS credentials not found.") from e
        except Exception as e:
            print(f"Error clearing objects in S3: {e}")


def hash_tuple(t: tuple) -> int:
    """
    Hash a tuple of hashable objects.
    """
    serialized_tuple = pickle.dumps(t)
    hash_object = hashlib.sha256()
    hash_object.update(serialized_tuple)
    return int(hash_object.hexdigest(), 16)


@dataclass
class Task(abc.ABC):
    task_name: str
    load_persisted_results: bool = False
    dependencies: tuple[type["Task"], ...] = field(default_factory=tuple)
    _base_recoverable_errors: set = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._base_recoverable_errors = {modal.exception.Error, KeyboardInterrupt}

    async def run(
        self,
        dependent_results: dict["Task", TaskResult],
    ) -> TaskResult:
        try:
            result = await self.run_implementation(dependent_results)
            return TaskResult(result=result, state=TaskResultKind.SUCCESS)
        except Exception as e:
            raise e
            if self._is_recoverable_error(e):
                return TaskResult(
                    result={"error": f"{e.__class__}, {e}"},
                    state=TaskResultKind.RECOVERABLE_ERROR,
                )
            else:
                # TODO log when errors occur here so we know to look at them. Consider scheduling email or similar
                return TaskResult(
                    result={"error": f"{e.__class__}, {e}"},
                    state=TaskResultKind.UNRECOVERABLE_ERROR,
                )

    @abstractmethod
    async def run_implementation(
        self, dependent_results: dict["Task", TaskResult]
    ) -> dict[str, any]:
        raise NotImplementedError

    @abstractmethod
    def recoverable_errors(self) -> set[type[Exception]]:
        raise NotImplementedError

    def _is_recoverable_error(self, error: Exception) -> bool:
        for recoverable_error in (
            self._base_recoverable_errors | self.recoverable_errors()
        ):
            if isinstance(error, recoverable_error):
                return True
        return False

    @abstractmethod
    def hashable_attrs(self) -> tuple:
        raise NotImplementedError

    def __hash__(self):
        """
        Hash the task based on its attributes. Note that we use `hash_tuple`, which gives a reproducible hash
        across Python processes, unlike the built-in `hash` function.
        """
        return hash_tuple(self.hashable_attrs())

    def __eq__(self, other):
        if isinstance(other, Task):
            return self.hashable_attrs() == other.hashable_attrs()
        return False


@dataclass
class TaskManager:
    tasks: list[type[Task]] = field(default_factory=list)
    serial_exe: bool = False
    task_results: dict[type[Task], TaskResult] = field(default_factory=dict)
    task_to_asynctask: dict[type[Task], asyncio.Task] = field(default_factory=dict)
    persistence: None | TaskResultPersistence = field(
        default_factory=lambda: S3TaskResultPersistence(
            "modal-dev-inspector-1234442"
        )  # TODO make configurable!!
    )
    write_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    write_executor: ThreadPoolExecutor = field(
        default_factory=lambda: ThreadPoolExecutor(max_workers=5)
    )

    @classmethod
    def with_s3_persistence(cls, bucket_name: str, *args, **kwargs):
        return cls(*args, persistence=S3TaskResultPersistence(bucket_name), **kwargs)

    async def run_tasks(self, run_id: str, resume: bool = False):
        if resume and self.persistence:
            # We can block the event loop with blocking IO when loading the state we aren't running
            # anything concurrent yet
            self.load_persisted_results(run_id)

        if self.persistence:
            writer_task = asyncio.create_task(self._write_task_results(run_id))

        try:
            if self.serial_exe:
                for task in self.tasks:
                    await self._schedule_and_await_task(task)
            else:
                await asyncio.gather(
                    *[self._schedule_and_await_task(task) for task in self.tasks]
                )
        finally:
            # Stop the writer task
            await self.write_queue.put(None)
            if self.persistence:
                await writer_task

        return self.task_results

    def load_persisted_results(self, run_id):
        print("Loading persisted results for resumption...")
        persisted_results = self.persistence.load_all_results(run_id)
        flattened_tasks = self.tasks
        print("Total tasks:", len(flattened_tasks))
        for task in flattened_tasks:
            task_hash_str = str(hash(task))
            if task.load_persisted_results and task_hash_str in persisted_results:
                print(f"Loaded results for task '{task.task_name}' from storage")
                self.task_results[task] = persisted_results[task_hash_str]
        print(
            f"Loaded results successfully for {len(self.task_results)} tasks from storage"
        )

    async def _schedule_and_await_task(self, task: type[Task]) -> asyncio.Task:
        asynctask = self._schedule_task_if_needed(task)
        return await asynctask

    def _schedule_task_if_needed(self, task: type[Task]) -> asyncio.Task:
        if self._can_skip_task(task):
            print(
                f"Skipping task '{task.task_name}'. It's state is '{self.task_results[task].state}'"
            )
            return asyncio.create_task(
                asyncio.sleep(0)
            )  # Create a dummy task to await. TODO see if we can remove

        if task not in self.task_to_asynctask:
            task_coroutine = self._run_task(task)
            self.task_to_asynctask[task] = asyncio.create_task(task_coroutine)
        return self.task_to_asynctask[task]

    def _can_skip_task(self, task: type[Task]) -> bool:
        task_result = self.task_results.get(task, None)
        if task_result is None:
            return False

        match task_result.state:
            case TaskResultKind.SUCCESS:
                return True
            case TaskResultKind.RECOVERABLE_ERROR:
                # TODO: Note, we'll rerun if there was a recoverable error, but we don't have the diff update flow yet, so
                # we're not re-running upstream tasks.
                return False
            case TaskResultKind.UNRECOVERABLE_ERROR:
                return True

    async def _run_task(self, task: type[Task]):
        """
        Run the task, ensuring that all dependencies run first.
        """
        if self.serial_exe:
            for dep_task in task.dependencies:
                await self._schedule_and_await_task(dep_task)
        else:
            dependent_tasks = [
                self._schedule_and_await_task(dep_task)
                for dep_task in task.dependencies
            ]
            await asyncio.gather(*dependent_tasks)

        print(f"Running task '{task.task_name}'...")
        result = await task.run(
            dependent_results={
                dep_task: self.task_results[dep_task] for dep_task in task.dependencies
            }
        )
        self.task_results[task] = result

        task_hash_str = str(hash(task))
        await self.write_queue.put((task_hash_str, result))

        return result

    async def _write_task_results(self, run_id: str):
        while True:
            item = await self.write_queue.get()
            if item is None:
                break
            task_id, result = item
            await asyncio.get_running_loop().run_in_executor(
                self.write_executor,
                self.persistence.save_task_result,
                run_id,
                task_id,
                result,
            )
        print("Writer task done")


def flatten_tasks(tasks: list[type[Task]]) -> list[type[Task]]:
    def _flatten(task: type[Task], seen: set[type[Task]]) -> list[type[Task]]:
        if task in seen:
            return []
        seen.add(task)
        return [task] + [t for dep in task.dependencies for t in _flatten(dep, seen)]

    seen = set()
    return [t for task in tasks for t in _flatten(task, seen)]
