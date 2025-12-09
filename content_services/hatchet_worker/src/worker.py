import truststore
from hatchet_client import hatchet
from workflows.auth0_sync_workflow import auth0_sync_task
from workflows.autodocs_functions import llm_generate_task
from workflows.autodocs_workflow import autodocs_task
from workflows.deep_context_functions import make_changelog_task
from workflows.inspector_functions import (
    codebase_tags_task,
    deep_context_docs_task,
    export_tech_docs_task,
    folder_doc_task,
    symbol_doc_task,
    tech_doc_task,
    toplevel_doc_task,
)
from workflows.inspector_workflow import inspector_task
from workflows.onboarding_workflows import run_codebase_connection_task
from workflows.pdf_processing_workflow import pdf_processing_task

truststore.inject_into_ssl()
def main() -> None:
    worker = hatchet.worker(
        "test-worker",
        slots=20,
        workflows=[
            pdf_processing_task,
            inspector_task,
            tech_doc_task,
            folder_doc_task,
            symbol_doc_task,
            toplevel_doc_task,
            autodocs_task,
            run_codebase_connection_task,
            llm_generate_task,
            make_changelog_task,
            deep_context_docs_task,
            export_tech_docs_task,
            codebase_tags_task,
            auth0_sync_task,
        ],
    )
    worker.start()


if __name__ == "__main__":
    main()
