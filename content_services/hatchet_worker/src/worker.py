from hatchet_client import hatchet
from workflows.first_workflow import my_task
from workflows.pdf_processing_workflow import pdf_processing_task


def main() -> None:
    worker = hatchet.worker(
        "test-worker", slots=1, workflows=[my_task, pdf_processing_task]
    )
    worker.start()


if __name__ == "__main__":
    main()
