import asyncio
import json
import time
from collections.abc import Generator
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import boto3
import pytest
from moto import mock_aws

from utils.dag import LiteNode, NodeKind
from utils.task import (
    LocalDiskTaskResultPersistence,
    S3TaskResultPersistence,
    Task,
    TaskManager,
    TaskResult,
)


class MockTaskResult:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

    def to_json(self) -> str:
        return json.dumps(self.data)

    @staticmethod
    def from_json(json_str: str) -> "MockTaskResult":
        data = json.loads(json_str)
        return MockTaskResult(data)


class TestLocalDiskTaskResultPersistence:
    @pytest.fixture
    def temp_dir(self) -> Generator[Path, None, None]:
        with TemporaryDirectory() as tmpdirname:
            yield Path(tmpdirname)

    @pytest.fixture
    def mock_task_result(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("utils.task.TaskResult", MockTaskResult)

    def test_save_and_load_task_result(
        self, temp_dir: Path, mock_task_result: None
    ) -> None:
        persistence = LocalDiskTaskResultPersistence(base_dir=temp_dir)
        run_id = "test_run"
        task_id = "test_task"
        result = MockTaskResult(data={"key": "value"})

        persistence.save_task_result(run_id, task_id, result)
        loaded_result = persistence.load_task_result(run_id, task_id)

        assert loaded_result is not None
        assert loaded_result.data == result.data

    def test_load_nonexistent_task_result(
        self, temp_dir: Path, mock_task_result: None
    ) -> None:
        persistence = LocalDiskTaskResultPersistence(base_dir=temp_dir)
        run_id = "test_run"
        task_id = "nonexistent_task"

        result = persistence.load_task_result(run_id, task_id)

        assert result is None

    def test_load_all_results(self, temp_dir: Path, mock_task_result: None) -> None:
        persistence = LocalDiskTaskResultPersistence(base_dir=temp_dir)
        run_id = "test_run"
        results = {
            "task_1": MockTaskResult(data={"key1": "value1"}),
            "task_2": MockTaskResult(data={"key2": "value2"}),
        }

        for task_id, result in results.items():
            persistence.save_task_result(run_id, task_id, result)

        loaded_results = persistence.load_all_results(run_id)

        assert len(loaded_results) == len(results)
        for task_id, result in results.items():
            assert task_id in loaded_results
            assert loaded_results[task_id].data == result.data

    def test_clear_all_results(self, temp_dir: Path, mock_task_result: None) -> None:
        persistence = LocalDiskTaskResultPersistence(base_dir=temp_dir)
        run_id = "test_run"
        results = {
            "task_1": MockTaskResult(data={"key1": "value1"}),
            "task_2": MockTaskResult(data={"key2": "value2"}),
        }

        for task_id, result in results.items():
            persistence.save_task_result(run_id, task_id, result)

        persistence.clear_all_results(run_id)
        loaded_results = persistence.load_all_results(run_id)

        assert len(loaded_results) == 0
        run_dir = persistence._get_run_dir(run_id)
        assert not run_dir.exists()


class TestS3TaskResultPersistence:
    @pytest.fixture
    def s3_bucket(self) -> Generator[str, None, None]:
        with mock_aws():
            s3_client = boto3.client("s3")
            bucket_name = "test-bucket"
            s3_client.create_bucket(Bucket=bucket_name)
            yield bucket_name

    @pytest.fixture
    def mock_task_result(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("utils.task.TaskResult", MockTaskResult)

    def test_save_and_load_task_result(
        self, s3_bucket: str, mock_task_result: None
    ) -> None:
        persistence = S3TaskResultPersistence(bucket_name=s3_bucket)
        run_id = "test_run"
        task_id = "test_task"
        result = MockTaskResult(data={"key": "value"})

        persistence.save_task_result(run_id, task_id, result)
        loaded_result = persistence.load_task_result(run_id, task_id)

        assert loaded_result is not None
        assert loaded_result.data == result.data

    def test_load_nonexistent_task_result(
        self, s3_bucket: str, mock_task_result: None
    ) -> None:
        persistence = S3TaskResultPersistence(bucket_name=s3_bucket)
        run_id = "test_run"
        task_id = "nonexistent_task"

        result = persistence.load_task_result(run_id, task_id)

        assert result is None

    def test_load_all_results(self, s3_bucket: str, mock_task_result: None) -> None:
        persistence = S3TaskResultPersistence(bucket_name=s3_bucket)
        run_id = "test_run"
        results = {
            "task_1": MockTaskResult(data={"key1": "value1"}),
            "task_2": MockTaskResult(data={"key2": "value2"}),
        }

        for task_id, result in results.items():
            persistence.save_task_result(run_id, task_id, result)

        loaded_results = persistence.load_all_results(run_id)

        assert len(loaded_results) == len(results)
        for task_id, result in results.items():
            assert task_id in loaded_results
            assert loaded_results[task_id].data == result.data

    def test_clear_all_results(self, s3_bucket: str, mock_task_result: None) -> None:
        persistence = S3TaskResultPersistence(bucket_name=s3_bucket)
        run_id = "test_run"
        results = {
            "task_1": MockTaskResult(data={"key1": "value1"}),
            "task_2": MockTaskResult(data={"key2": "value2"}),
        }

        for task_id, result in results.items():
            persistence.save_task_result(run_id, task_id, result)

        persistence.clear_all_results(run_id)
        loaded_results = persistence.load_all_results(run_id)

        assert len(loaded_results) == 0


class SleepTask(Task):
    def __init__(
        self,
        task_name: str,
        sleep_time: float,
        dependencies: tuple[Task, ...] | None = None,
    ) -> None:
        dependencies = dependencies or tuple()

        # NOTE: we must give unique nodes to the tasks because our hasing scheme
        # assumes that nodes will not have multiple tasks of the same name with the same dependencies.
        # TODO: revist in the future if needed.
        super().__init__(
            task_name=task_name,
            node=LiteNode(kind=NodeKind.FILE, root_rel_path=Path(task_name)),
            dependencies=dependencies,
        )
        self.sleep_time = sleep_time

        self.captured_io_results = None  # Captures `dependent_io_results` in `post_run_io` for assertions about what was injected

    async def run_implementation(
        self, dependent_results: dict[Task, TaskResult]
    ) -> dict[str, Any]:
        start_time = time.time()
        await asyncio.sleep(self.sleep_time)
        end_time = time.time()
        return {"start_time": start_time, "completed_at": end_time}

    def recoverable_errors(self) -> set[type[Exception]]:
        return set()

    async def post_run_io(
        self,
        task_result: TaskResult,
        dependent_io_results: dict["Task", dict[str, any]],
    ) -> dict[str, any]:
        # Store the dependent IO results for validation in the test
        self.captured_io_results = dependent_io_results
        return {"io_completed": True}


class TestTaskManager:
    @pytest.fixture
    def setup_tasks(self) -> tuple[TaskManager, Task, Task, Task]:
        task1 = SleepTask(task_name="task1", sleep_time=1)
        task2 = SleepTask(task_name="task2", sleep_time=1.5, dependencies=(task1,))
        task3 = SleepTask(task_name="task3", sleep_time=1, dependencies=(task1,))

        tasks = [task1, task2, task3]

        task_manager = TaskManager(tasks=tasks, serial_exe=False, persistence=None)
        return task_manager, task1, task2, task3

    @pytest.mark.asyncio
    async def test_task_dependency_basic(
        self, setup_tasks: tuple[TaskManager, Task, Task, Task]
    ) -> None:
        task_manager, task1, task2, task3 = setup_tasks

        global_start_time = time.time()
        await task_manager.run_tasks(run_id="test_run")

        task1_result = task_manager.task_results[task1].result
        task2_result = task_manager.task_results[task2].result
        task3_result = task_manager.task_results[task3].result

        task1_start_time = task1_result["start_time"]
        task1_completion_time = task1_result["completed_at"]
        task2_start_time = task2_result["start_time"]
        task2_completion_time = task2_result["completed_at"]
        task3_start_time = task3_result["start_time"]
        task3_completion_time = task3_result["completed_at"]

        assert task1_start_time >= global_start_time
        assert task1_completion_time >= task1_start_time + 1
        assert task2_start_time >= task1_completion_time
        assert task2_completion_time >= task2_start_time + 1.5
        assert task3_start_time >= task1_completion_time
        assert task3_completion_time >= task3_start_time + 1

        # Ensure task3 runs concurrently with task2
        assert abs(task3_start_time - task2_start_time) < 0.1

        print(f"Task 1 started at: {task1_start_time}")
        print(f"Task 1 completed at: {task1_completion_time}")
        print(f"Task 2 started at: {task2_start_time}")
        print(f"Task 2 completed at: {task2_completion_time}")
        print(f"Task 3 started at: {task3_start_time}")
        print(f"Task 3 completed at: {task3_completion_time}")

        assert task2_completion_time >= global_start_time + 2
        assert task3_completion_time >= global_start_time + 2

    @pytest.mark.asyncio
    async def test_post_run_io_injection(
        self, setup_tasks: tuple[TaskManager, Task, Task, Task]
    ) -> None:
        """
        Tests that `post_run_io` is called and IO results are injected correctly
        from any dependencies that have completed.
        """
        task_manager, task1, task2, task3 = setup_tasks

        # Run the tasks to trigger `post_run_io`
        await task_manager.run_tasks(run_id="test_run_io")

        print(f"Task 1 IO Result: {task1.captured_io_results}")
        print(f"Task 2 IO Result: {task2.captured_io_results}")
        print(f"Task 3 IO Result: {task3.captured_io_results}")

        # Ensure task1 has no captured IO results since it has no dependencies
        assert task1.captured_io_results == dict()

        # Validate that `post_run_io` was called and IO results were injected for dependencies
        assert task2.captured_io_results == {task1: {"io_completed": True}}
        assert task3.captured_io_results == {task1: {"io_completed": True}}

    # Test rerunning will rerun tasks that ended in recoverable error but not the others!

    # class TestErrorPropagation:
    #     class ErrorTask(Task):
    #         def __init__(self, task_name: str, error: Exception):
    #             super().__init__(task_name=task_name)
    #             self.error = error
    #
    #         async def run_implementation(self, dependent_results: dict["Task", TaskResult]) -> dict[str, any]:
    #             raise self.error
    #
    #         def recoverable_errors(self) -> set[type[Exception]]:
    #             return {type(self.error)}
    #
    #         def hashable_attrs(self) -> tuple:
    #             return (self.task_name, self.error)
    #
    #     @pytest.mark.asyncio
    #     async def test_error_propagation(self):
    #         error_task = self.ErrorTask(task_name="error_task", error=RuntimeError("Error message"))
    #         task_manager = TaskManager(tasks=[error_task], serial_exe=False, persistence=None)
