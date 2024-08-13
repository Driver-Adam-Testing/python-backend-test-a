import re

import modal
from openai import OpenAI

from .tool import Tool


def format_search_results(results):
    if results.get("results") == []:
        return "Search returned no results"
    formatted_results = []
    for result in results.get("results"):
        content = result.get("content", "")
        metadata = result.get("metadata", {})
        content_type = metadata.get("content_type", "")
        relative_path = metadata.get("relative_path", "")

        formatted_result = f"""<result>
            <content>{content}</content>
            <content_type>{content_type}</content_type>
            <relative_path>{relative_path}</relative_path>
        </result>
        """
        formatted_results.append(formatted_result.strip())

    return "\n".join(formatted_results)


def execute_backend_search(
    agent_context,
    search_text: str,
    content_types: list[str] | None = None,
    relative_path: str | None = None,
    result_limit: int = 10,
):
    # backend_host = os.getenv("DRIVER_API_URL")
    # if not backend_host:
    #     raise OSError("DRIVER_API_URL environment variable is not set.")
    payload = {
        "query": search_text,
        "result_limit": result_limit,
        "content_type": content_types,
        "workspace_id": str(agent_context.workspace_id),
        "codebase_id": str(agent_context.codebase_id),
        "relative_path": relative_path,
        "algorithm": "hybrid",
    }
    search_function = modal.Function.lookup("comprehender", "search")
    response = search_function.remote(payload)
    return format_search_results(response.dict())


def search_tech_docs(agent_context, search_text: str, rationale: str) -> str:
    return execute_backend_search(
        agent_context=agent_context,
        search_text=f"`{search_text}`. information on {search_text} because {rationale}",
        content_types=["FILE_SUMMARY", "CODE_SYMBOL"],
    )


search_tech_docs_tool = Tool(
    function=search_tech_docs,
    description="""Search the codebase's technical documentation.""",
)


def search_source_code(agent_context, search_text: str, rationale: str) -> str:
    return execute_backend_search(
        agent_context=agent_context,
        search_text=f"`{search_text}` information on {search_text}",
        content_types=["SOURCE_CODE"],
    )


search_source_code_tool = Tool(
    function=search_source_code, description="""Search the codebase's source code."""
)


def think(agent_context, thought: str) -> str:
    return thought


think_tool = Tool(
    function=think,
    description="Think about the actions you are about to take. Explain why you are using the tools to get more specific about the codebase, and how it helps avoid generalized content.",
)


def query_uploaded_pdf_files(
    agent_context, file_ids: list[str], query: str, rationale: str = None
) -> str:
    client = OpenAI()
    # TODO: make typehints consistent with openai
    if isinstance(file_ids, str):
        file_ids = re.findall(r"file-\w{24}", file_ids)
    elif isinstance(file_ids, dict):
        file_ids = re.findall(r"file-\w{24}", str(file_ids))
    elif isinstance(file_ids, list):
        file_ids = re.findall(r"file-\w{24}", str(file_ids))

    if len(file_ids) == 0:
        return 'file_ids improperly formatted. File ids are 24 character strings prefixed with "file-"'

    try:
        if file_ids:
            assistant = client.beta.assistants.create(
                name="PDF Comprehender",
                instructions="You are an expert technical writer.",
                tools=[{"type": "retrieval"}],
                model="gpt-4-turbo-preview",
                file_ids=file_ids,
            )
            thread = client.beta.threads.create()
            client.beta.threads.messages.create(
                thread_id=thread.id, role="user", content=query
            )
            run = client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant.id,
                instructions="you're an expert technical writer who can understand documents.",
            )
            if run.status == "completed":
                messages = client.beta.threads.messages.list(thread_id=thread.id)
                return messages.data[0].content[0].text.value
        return ""
    except Exception as e:
        return str(e)


query_uploaded_pdf_files_tool = Tool(
    function=query_uploaded_pdf_files,
    description="Ask an AI assistant a question about the specific auxiliary files. The file_ids parameter is an array of file_ids.",
)


def search_source_code_and_descriptions(
    agent_context, query: str, rationale: str
) -> dict:
    return execute_backend_search(
        agent_context=agent_context,
        result_limit=20,
        search_text=f"`{query}`. information on {query} because {rationale}",
    )


deep_rag_tool = Tool(
    function=search_source_code_and_descriptions,
    description="Query the file summaries and then query the source code using all the relative file paths of the results. Rationale is why you searched for it, and how it makes your knowledge base more specific to the codebase.",
)


def search_pdf_summaries(agent_context, query: str, rationale: str) -> dict:
    return execute_backend_search(
        agent_context=agent_context,
        result_limit=20,
        search_text=f"`{query}`. information on {query} because {rationale}",
        content_types=[
            "PDF_SUMMARY",  # TODO: Look into why this isn't importing when deployed but is when it's local
        ],
    )


search_pdf_summaries_tool = Tool(
    function=search_pdf_summaries,
    description="Get search results from the page summaries from all the uploaded pdfs",
)


def list_files(agent_context, rationale: str) -> str:
    return str(agent_context.collection.get_file_system(agent_context.codebase_id))


list_files_tool = Tool(
    function=list_files,
    description="list all the files and folders in the codebase. This tool is great for getting an overview of the file system in a codebase. Use rationale to describe why you needed the list of files.",
)


def echo(agent_context, input: str) -> str:
    return str(input)


echo_tool = Tool(
    function=echo,
    description="Echoes the input string.",
)
