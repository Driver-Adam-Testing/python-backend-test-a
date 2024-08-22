from urllib.parse import unquote, urlparse

from pydantic import UUID4, BaseModel
from shared import prompts
from shared.agent import Agent
from shared.agent.agent_tools import (
    deep_rag_tool,
    list_files_tool,
    query_uploaded_pdf_files,
    search_pdf_summaries_tool,
    search_source_code_tool,
)
from shared.agent.tool import Tool


class CreateAppNoteRequest(BaseModel):
    workspace_id: UUID4
    prompt: str
    codebase_id: UUID4 = None
    options: dict = {}
    model: str = "gpt-4o"


def create_app_note(request: CreateAppNoteRequest):
    # TODO: Totally remove Workspace and replace with search scopes and org
    agent = Agent(
        workspace_id=request.workspace_id,
        codebase_id=request.codebase_id,
        tools=[
            deep_rag_tool,
            search_source_code_tool,
        ],
        max_iterations=5,
        model=request.model,
    )
    file_ids = agent.agent.collection.get_uploaded_files(request.codebase_id)
    file_list_length = len(
        agent.agent.collection.get_file_system(agent.agent.codebase_id)
    )
    if file_list_length < 200:
        agent.agent.tools.append(list_files_tool)
    if file_ids:
        available_files = []
        agent.agent.tools.append(search_pdf_summaries_tool)
        for file in file_ids:
            try:
                parsed_url = urlparse(file.misc_metadata.get("url"))
                # Extract the path component
                path = parsed_url.path
                # Split the path to get the filename
                filename = path.split("/")[-1]
                # Decode any URL-encoded characters in the filename
                available_files.append(
                    f"{unquote(filename)}: {file.misc_metadata.get('file_id')}"
                )
            except Exception:
                try:
                    available_files.append(
                        {
                            "name": file.misc_metadata.get("url"),
                            "file_id": file.misc_metadata.get("file_id"),
                        }
                    )
                except Exception:
                    pass
        for i in range(0, len(available_files), 5):
            # TODO: Fix this so it's less hacky to get around the description limits.
            file_subset = available_files[i : i + 5]
            pdf_tool = Tool(
                function=query_uploaded_pdf_files,
                description=f"Ask an OpenAI assistant a question about uploaded auxiliary files. The file_ids parameter is an array of file_ids. AVAILABLE FILE LIST: {file_subset}",
            )
            agent.agent.tools.append(pdf_tool)
        agent.add_message(
            {
                "role": "system",
                "content": "use the uploaded files when the source code and descriptions provide insufficient context. Be clear and specific with the query.",
            }
        )
    agent.add_message(prompts.interface.batch_tools.MESSAGE)
    agent.add_message(prompts.interface.technical_context_interface.MESSAGE)
    agent.add_message(prompts.voice.software_engineer.MESSAGE)
    agent.add_message(prompts.audience.software_engineer.MESSAGE)
    agent.add_message(prompts.audience.software_engineer.ASSISTANT_MESSAGE)

    agent.invoke(
        f"Using only the results provided by the search tools and file list, plan out a concise, comprehensive answer to the following prompt: \n\n{request.prompt}\n\n. Let's think step by step. The final document will be an application note, which is an in-depth, organized, highly technical document about a specific codebase that can be searched."
    )

    document = agent.invoke(
        f"""Based on the previous thought, respond with the final document in it's entirety. Remove outer ```markdown``` tags. Format it for markdown rendering. Since this document will be available in a larger group of technical documents, remove any conclusion, introduction, reference, or appendix sections. Search for additional context to deepen your understanding and provide snippets and examples. Follow the previous prompts and use the previous tool responses. Write the document while ensuring the most efficient writing, exampled, and source code rich way to answer the prompt: \n\n{request.prompt}"""
    )

    copyeditor = Agent(
        workspace_id=request.workspace_id,
        codebase_id=request.codebase_id,
        max_iterations=1,
        model=request.model,
    )
    copyeditor.add_message(prompts.voice.copy_editor.MESSAGE)
    copyeditor.add_message(prompts.voice.copy_editor_remove_speculation.MESSAGE)
    copyeditor.add_message(prompts.voice.copy_editor_remove_useless_language.MESSAGE)
    copyeditor.add_message(prompts.audience.software_engineer.MESSAGE)
    copyeditor.add_message(prompts.audience.software_engineer.ASSISTANT_MESSAGE)

    results = copyeditor.invoke(
        f"Edit the following document, and remove explainations of the document: \n\n {document}"
    )

    title = copyeditor.invoke(
        "What is an appropriate 6-8 word title for the document? (don't use quotation marks)"
    )
    description = copyeditor.invoke("write a 1-2 sentence description of the document?")

    return {"name": title, "content": results, "description": description}
