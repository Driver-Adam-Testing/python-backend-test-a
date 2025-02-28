import time

from prettytable import PrettyTable
from shared.interfaces.agents.data_scope import DataScope
from shared.v3.app.pipelines.get_information_set_definitions import (
    get_information_set_definitions,
)
from shared.v3.app.pipelines.interfaces.pipeline_request import (
    PipelineExecutionRequest,
)
from shared.v3.llms.clients.llm_client import LlmClient

PROMPTS = [
    "Summarize the project's purpose and target audience in one sentence.",
    "List all core modules with their responsibilities, key functions, and dependencies. Format: Table with columns: Module Name | Responsibilities | Key Functions | Dependencies",
    "Describe in two sentences how the configuration files are structured and managed throughout the codebase.",
    "Document the error handling strategy by explaining how errors are caught, logged, and propagated. Include code block examples demonstrating these techniques. Format: 2-3 paragraphs with embedded code blocks.",
    "Provide a brief paragraph describing the testing framework used in the project and its main advantages.",
    "Generate a sequence diagram that visualizes the full request lifecycle from client to server, including middleware and service interactions. Format: Mermaid diagram preceded by a short explanatory text.",
    "List all public API endpoints with a short description of each endpoints function.",
    "Detail the data models employed in the system and their relationships to one another. Format: Table with columns: Model Name | Key Fields | Relationships | Purpose",
    "Explain in one sentence how the build process for the project is organized.",
    "Describe the logging mechanism and its configuration in three sentences, and provide a code snippet that shows an example log setup. Format: Paragraph explanation with an accompanying code block.",
    "Summarize the dependency management strategy used to ensure compatibility across project modules.",
    "Create a bullet list of all external services integrated into the application, including their endpoints and the methods of authentication they require.",
    "Describe the continuous integration and deployment (CI/CD) process in the project. Include details on how code is tested, built, and deployed. Format: 3-4 sentences in a single paragraph.",
    "Outline the security measures implemented within the application, focusing on encryption, access control, and authentication. Format: Paragraph explanation.",
    "Provide a detailed description of the caching strategy used in the codebase, including the technology stack and cache invalidation processes. Include code examples where appropriate. Format: Paragraph with embedded code snippets.",
    "Explain how configuration is managed across different environments (development, staging, production) in one sentence.",
    "Document the management of user sessions and state persistence in the application. Include code block examples followed by a brief explanatory paragraph.",
    "Offer a one-sentence summary of the primary CLI commands available in the project and their purposes.",
    "Describe the version control workflow, detailing branch management, merge strategies, and release tagging processes. Format: Paragraph explanation.",
    "List the system requirements necessary to run the application, including hardware and software prerequisites. Format: Table with columns: Requirement Type | Description | Minimum Specification | Recommended Specification",
]

BEFORE = [
    "",
    "",
    "Untitled document",
    "This section contains the initial setup and configuration details for the electrical components.",
    "The following paragraphs describe the installation process for the electrical components.",
    "Here you will find the prerequisites and requirements for setting up the electrical components.",
    "This part of the document provides an overview of the electrical components and their specifications.",
    "The initial steps for configuring the electrical components are outlined in this section.",
]

AFTER = [
    "",
    "EOF",
    ".",
    ";",
    ":",
    "The subsequent sections cover the troubleshooting and maintenance procedures for the electrical components.",
    "Following this, you will find the detailed usage instructions for the electrical components.",
    "The next part of the document includes the safety guidelines and best practices for handling the electrical components.",
    "In the following paragraphs, the performance metrics and benchmarks for the electrical components are discussed.",
    "The final sections provide additional resources and references for further information on the electrical components.",
]


def inject_pipeline_requests():
    pipeline_requests = []
    for _ in range(10):
        import random

        pipeline_requests.append(
            {
                "prompt": random.choice(PROMPTS),
                "node_ids": ["bce8a419-4cd4-4717-8d20-08b92ee97c29"],
                "steps": [],
                "block_kind": "ANY",
                "context": {
                    "selected_text": "",
                    "before_selected_text": random.choice(BEFORE),
                    "after_selected_text": random.choice(AFTER),
                },
            }
        )
    return pipeline_requests


def run_and_time_pipeline():
    pipeline_requests = inject_pipeline_requests()
    client_timings = {}

    def process_request(request, client):
        start_time = time.time()
        try:
            response = get_information_set_definitions(
                PipelineExecutionRequest(
                    original_prompt=request["prompt"],
                    text_before_selection=request["context"]["before_selected_text"],
                    text_after_selection=request["context"]["after_selected_text"],
                    datascope=DataScope(
                        node_ids=request["node_ids"],
                        organization_id="dummy_org_id",
                        user_id="dummy_user_id",
                    ),
                )
            )

            GREEN = "\033[92m"
            BLUE = "\033[94m"
            YELLOW = "\033[93m"
            CYAN = "\033[96m"
            RESET = "\033[0m"
            print(BLUE + "Prompt:" + RESET)
            print(request["prompt"])
            print(BLUE + "Before Selected Text:" + RESET)
            print(request["context"]["before_selected_text"])
            print(BLUE + "After Selected Text:" + RESET)
            print(request["context"]["after_selected_text"])

            print(BLUE + "Information Sets with Parameters:" + RESET)
            for info_set in response["information_sets_with_parameters"]:
                print(YELLOW + "Information Set:" + RESET)
                print(f"  Name: {info_set['information_set'].name}")
                print(f"  Description: {info_set['information_set'].description}")
                print(f"  Rationale: {info_set['information_set'].rationale}")

                print(CYAN + "  Parameters:" + RESET)
                params = info_set["parameters"]
                print(GREEN + f"    Query Strings: {params.query_strings}" + RESET)
                print(
                    GREEN + f"    Comparison Affirm: {params.comparison_affirm}" + RESET
                )
                print(
                    GREEN + f"    Comparison Negate: {params.comparison_negate}" + RESET
                )
                print(GREEN + f"    Source Bounding: {params.source_bounding}" + RESET)
                print(GREEN + f"    Query Type: {params.query_type}" + RESET)
                print(
                    GREEN + f"    Element Analysis: {params.element_analysis}" + RESET
                )
                print(GREEN + f"    Exhaustiveness: {params.exhaustiveness}" + RESET)
                print(GREEN + f"    Rationale: {params.rationale}" + RESET)
        except Exception as e:
            import traceback

            print(f"An error occurred while processing the request: {e}")
            traceback.print_exc()
            raise e
        end_time = time.time()
        return end_time - start_time

    llm_clients = [
        LlmClient.gpt_4o(),
        LlmClient.gpt_4o_mini(),
        LlmClient.gpt_4o_mini_chat(),
        LlmClient.o1(),
        LlmClient.o1_mini(),
        LlmClient.o3_mini(),
    ]

    for client in llm_clients:
        for request in pipeline_requests:
            time_taken = process_request(request, client)
            client_id = client.config.model_name
            if client_id not in client_timings:
                client_timings[client_id] = []
            client_timings[client_id].append(time_taken)
            input()

    table = PrettyTable()
    table.field_names = ["Client ID", "Best Time", "Average Time", "Worst Time"]

    for client_id, times in client_timings.items():
        best_time = round(min(times), 2)
        worst_time = round(max(times), 2)
        average_time = round(sum(times) / len(times), 2)
        table.add_row([client_id, best_time, average_time, worst_time])

    print(table)


if __name__ == "__main__":
    run_and_time_pipeline()
