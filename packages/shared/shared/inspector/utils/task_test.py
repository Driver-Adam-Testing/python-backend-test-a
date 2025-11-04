import asyncio
import time
from collections.abc import Generator
from pathlib import Path
from tempfile import TemporaryDirectory

import boto3
import pytest
from moto import mock_aws

from utils.dag import LiteNode, NodeKind
from utils.task import (
    LocalDiskTaskResultPersistence,
    S3TaskResultPersistence,
    SerializationMethod,
    Task,
    TaskManager,
    TaskResult,
)


class TestLocalDiskTaskResultPersistence:
    @pytest.fixture
    def temp_dir(self) -> Generator[Path, None, None]:
        with TemporaryDirectory() as tmpdirname:
            yield Path(tmpdirname)

    def test_save_and_load_task_result_json(self, temp_dir: Path) -> None:
        persistence = LocalDiskTaskResultPersistence(base_dir=temp_dir)
        run_id = "test_run"
        task_id = "test_task"
        result = TaskResult(
            data={"key": "value"}, serialization=SerializationMethod.JSON
        )

        persistence.save_task_result(run_id, task_id, result)
        loaded_result = persistence.load_task_result(run_id, task_id)

        assert loaded_result is not None
        assert loaded_result.data == result.data

    def test_save_and_load_task_result_pickle(self, temp_dir: Path) -> None:
        persistence = LocalDiskTaskResultPersistence(base_dir=temp_dir)
        run_id = "test_run"
        task_id = "test_task"
        result = TaskResult(
            data={"key": "value"}, serialization=SerializationMethod.PICKLE
        )

        persistence.save_task_result(run_id, task_id, result)
        loaded_result = persistence.load_task_result(run_id, task_id)

        assert loaded_result is not None
        assert loaded_result.data == result.data

    def test_load_nonexistent_task_result(self, temp_dir: Path) -> None:
        persistence = LocalDiskTaskResultPersistence(base_dir=temp_dir)
        run_id = "test_run"
        task_id = "nonexistent_task"

        result = persistence.load_task_result(run_id, task_id)

        assert result is None


class TestS3TaskResultPersistence:
    @pytest.fixture
    def s3_bucket(self) -> Generator[str, None, None]:
        with mock_aws():
            s3_client = boto3.client("s3")
            bucket_name = "test-bucket"
            s3_client.create_bucket(Bucket=bucket_name)
            yield bucket_name

    def test_save_and_load_task_result_json(
        self,
        s3_bucket: str,
    ) -> None:
        persistence = S3TaskResultPersistence(bucket_name=s3_bucket)
        run_id = "test_run"
        task_id = "test_task"
        result = TaskResult(
            data={"key": "value"}, serialization=SerializationMethod.JSON
        )

        persistence.save_task_result(run_id, task_id, result)
        loaded_result = persistence.load_task_result(run_id, task_id)

        assert loaded_result is not None
        assert loaded_result.data == result.data

    def test_save_and_load_task_result_pickle(
        self,
        s3_bucket: str,
    ) -> None:
        persistence = S3TaskResultPersistence(bucket_name=s3_bucket)
        run_id = "test_run"
        task_id = "test_task"
        result = TaskResult(
            data={"key": "value"}, serialization=SerializationMethod.PICKLE
        )

        persistence.save_task_result(run_id, task_id, result)
        loaded_result = persistence.load_task_result(run_id, task_id)

        assert loaded_result is not None
        assert loaded_result.data == result.data

    def test_load_nonexistent_task_result(self, s3_bucket: str) -> None:
        persistence = S3TaskResultPersistence(bucket_name=s3_bucket)
        run_id = "test_run"
        task_id = "nonexistent_task"

        result = persistence.load_task_result(run_id, task_id)

        assert result is None


class SleepTask(Task):
    def __init__(
        self,
        task_name: str,
        sleep_time: float,
        dependencies: tuple[Task, ...] | None = None,
        work_units: int = 1,
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
        self._work_units = work_units

        self.captured_io_results = None  # Captures `dependent_io_results` in `post_run_io` for assertions about what was injected

    async def run_implementation(
        self, dependent_results: dict[Task, TaskResult]
    ) -> TaskResult:
        start_time = time.time()
        await asyncio.sleep(self.sleep_time)
        end_time = time.time()
        return TaskResult(
            data={"start_time": start_time, "completed_at": end_time},
            serialization=SerializationMethod.JSON,
        )

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

    @property
    def work_units(self) -> int:
        return self._work_units


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

        task1_result = task_manager.task_results[task1].data
        task2_result = task_manager.task_results[task2].data
        task3_result = task_manager.task_results[task3].data

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
