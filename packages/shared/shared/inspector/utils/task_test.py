import asyncio
import time
from collections.abc import Generator
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pytest
from shared.inspector.utils.dag import LiteNode, NodeKind
from shared.inspector.utils.task import (
    LocalDiskTaskResultPersistence,
    SerializationMethod,
    Task,
    TaskManager,
    TaskResult,
)


class MockTask(Task):
    def __init__(self, task_name: str, test_data: dict[str, Any]) -> None:
        super().__init__(
            task_name=task_name,
            node=LiteNode(kind=NodeKind.FILE, root_rel_path=Path(task_name)),
            dependencies=tuple(),
        )
        self.test_data = test_data

    async def run_implementation(
        self, dependent_results: dict[Task, TaskResult]
    ) -> TaskResult:
        return TaskResult(data=self.test_data, serialization=SerializationMethod.JSON)

    async def post_run_io(self, task_result: TaskResult) -> dict[str, Any]:
        return {"io_completed": True}

    def load_result(self) -> None | TaskResult:
        return None

    @property
    def work_units(self) -> int:
        return 1


class TestLocalDiskTaskResultPersistence:
    @pytest.fixture
    def temp_dir(self) -> Generator[Path, None, None]:
        with TemporaryDirectory() as tmpdirname:
            yield Path(tmpdirname)

    def test_save_and_load_task_result_json(self, temp_dir: Path) -> None:
        persistence = LocalDiskTaskResultPersistence(base_dir=temp_dir)
        run_id = "test_run"
        task = MockTask(task_name="test_task", test_data={"key": "value"})
        result = TaskResult(
            data={"key": "value"}, serialization=SerializationMethod.JSON
        )

        persistence.save_task_result(run_id, result, task)
        loaded_result = persistence.load_task_result(run_id, task)

        assert loaded_result is not None
        assert loaded_result.data == result.data

    def test_save_and_load_task_result_pickle(self, temp_dir: Path) -> None:
        persistence = LocalDiskTaskResultPersistence(base_dir=temp_dir)
        run_id = "test_run"
        task = MockTask(task_name="test_task", test_data={"key": "value"})
        result = TaskResult(
            data={"key": "value"}, serialization=SerializationMethod.PICKLE
        )

        persistence.save_task_result(run_id, result, task)
        loaded_result = persistence.load_task_result(run_id, task)

        assert loaded_result is not None
        assert loaded_result.data == result.data

    def test_load_nonexistent_task_result(self, temp_dir: Path) -> None:
        persistence = LocalDiskTaskResultPersistence(base_dir=temp_dir)
        run_id = "test_run"
        task = MockTask(task_name="nonexistent_task", test_data={})

        result = persistence.load_task_result(run_id, task)

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

        # NOTE: we must give unique nodes to the tasks because our hashing scheme
        # assumes that nodes will not have multiple tasks of the same name with the same dependencies.
        # TODO: revisit in the future if needed.
        super().__init__(
            task_name=task_name,
            node=LiteNode(kind=NodeKind.FILE, root_rel_path=Path(task_name)),
            dependencies=dependencies,
        )
        self.sleep_time = sleep_time
        self._work_units = work_units

        self.post_run_io_called = False
        self.received_task_result = None
        self.dependency_results_received = None

    def recoverable_errors(self) -> set[type[Exception]]:
        return set()

    def load_result(self) -> None | TaskResult:
        return None

    async def run_implementation(
        self, dependent_results: dict[Task, TaskResult]
    ) -> TaskResult:
        start_time = time.time()
        await asyncio.sleep(self.sleep_time)
        end_time = time.time()

        # Capture dependency results for testing
        self.dependency_results_received = dependent_results.copy()

        return TaskResult(
            data={"start_time": start_time, "completed_at": end_time},
            serialization=SerializationMethod.JSON,
        )

    async def post_run_io(self, task_result: TaskResult) -> dict[str, Any]:
        self.post_run_io_called = True
        self.received_task_result = task_result
        return {"io_completed": True, "task_data": task_result.data}

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
    async def test_post_run_io_execution(
        self, setup_tasks: tuple[TaskManager, Task, Task, Task]
    ) -> None:
        """
        Tests that post_run_io is called for each task after execution.
        """
        task_manager, task1, task2, task3 = setup_tasks

        await task_manager.run_tasks(run_id="test_run_io")

        # Verify all tasks have IO results stored in TaskManager
        assert task1 in task_manager.task_io_results
        assert task2 in task_manager.task_io_results
        assert task3 in task_manager.task_io_results
        # Verify IO results contain expected data
        assert task_manager.task_io_results[task1]["io_completed"] is True
        assert task_manager.task_io_results[task2]["io_completed"] is True
        assert task_manager.task_io_results[task3]["io_completed"] is True

    @pytest.mark.asyncio
    async def test_task_dependency_result_injection(
        self, setup_tasks: tuple[TaskManager, Task, Task, Task]
    ) -> None:
        """
        Tests that tasks receive results from their dependencies during execution.
        """
        task_manager, task1, task2, task3 = setup_tasks

        await task_manager.run_tasks(run_id="test_dependency_injection")

        # task1 has no dependencies, should receive empty dict
        assert task1.dependency_results_received == {}

        # task2 depends on task1, should receive task1's result
        assert task1 in task2.dependency_results_received
        assert (
            task2.dependency_results_received[task1].data
            == task_manager.task_results[task1].data
        )

        # task3 depends on task1, should receive task1's result
        assert task1 in task3.dependency_results_received
        assert (
            task3.dependency_results_received[task1].data
            == task_manager.task_results[task1].data
        )
