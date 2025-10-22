from hatchet_client import hatchet
from workflows.first_workflow import my_task
from workflows.inspector_functions import (
    folder_doc_task,
    symbol_doc_task,
    tech_doc_task,
    toplevel_doc_task,
)
from workflows.inspector_workflow import inspector_task
from workflows.pdf_processing_workflow import pdf_processing_task


def main() -> None:
    worker = hatchet.worker(
        "test-worker",
        slots=5,
        workflows=[
            my_task,
            pdf_processing_task,
            inspector_task,
            tech_doc_task,
            folder_doc_task,
            symbol_doc_task,
            toplevel_doc_task,
        ],
    )
    worker.start()


if __name__ == "__main__":
    main()
