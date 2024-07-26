import re
from urllib.parse import unquote, urlparse

from database.models_v1 import ContentType
from pydantic import UUID4, BaseModel
from shared import prompts
from shared.agent import Agent
from shared.agent.agent_tools import execute_backend_search

# TODO: something is wrong with options defaulting to {}


class RunAgentRequest(BaseModel):
    workspace_id: UUID4
    codebase_id: UUID4 = None
    prompt: str | None
    options: dict = {}


def run_agent(request: RunAgentRequest):
    workspace_id = request.workspace_id
    prompt = request.prompt
    codebase_id = request.codebase_id
    options = request.options if request.options else {}

    # TODO: figure out what KIND of request it probably is.
    # figure out if it's complex enough to take multiple iterations
    # Should RAG ahead of time
    # Does it have references to files / folders / aux docs / symbols?
    # text_input overwrites prompt if its there
    if options.get("text_input"):
        prompt = options.get("text_input")
    model = options.get("model", "gpt-4o")
    # Break out the options
    before_selected_text = options.get("before_selected_text", None)
    after_selected_text = options.get("after_selected_text", None)
    selected_text = options.get("selected_text", None)
    relative_path = options.get("relative_path", None)
    print(
        "before_selected_text",
        before_selected_text,
        "selected_text",
        selected_text,
        "after_selected_text",
        after_selected_text,
    )
    print("relative_path", relative_path, "prompt", prompt)

    if relative_path == "executive-summary" or relative_path == "entry-point":
        relative_path = None

    agent = Agent(
        workspace_id=workspace_id,
        codebase_id=codebase_id,
        max_iterations=1,
        model=model,
    )
    agent.add_message(prompts.interface.technical_context_interface.MESSAGE)
    agent.add_message(prompts.voice.copy_editor_remove_speculation.MESSAGE)
    agent.add_message(prompts.voice.copy_editor_remove_useless_language.MESSAGE)
    agent.add_message(
        {
            "role": "user",
            "content": "The following is search context taken from the codebase descriptions, source code, and pdf summaries: \n\n"
            + execute_backend_search(
                agent.agent,
                search_text=f"{prompt} {selected_text if selected_text else ''}",
                content_types=[
                    ContentType.CODE_SYMBOL.value,
                    ContentType.FILE_SUMMARY.value,
                    "PDF_SUMMARY",
                    ContentType.SOURCE_CODE.value,
                ],
                result_limit=25,
                relative_path=relative_path,
            ),
        }
    )
    file_ids = agent.agent.collection.get_uploaded_files(request.codebase_id)
    pdf_prompt = ""
    if file_ids and not relative_path:
        # TODO: Take all this out and make pdf search less of a band-aid

        from openai import OpenAI

        try:
            if file_ids:
                available_files = []
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
            client = OpenAI()

            file_ids = [
                file.misc_metadata.get("file_id")
                for file in file_ids
                if file.misc_metadata.get("file_id", None) is not None
            ]
            file_selection_agent = Agent(
                workspace_id=workspace_id, codebase_id=codebase_id, max_iterations=1
            )
            file_results = file_selection_agent.invoke(
                f"given the list of files: {available_files}, return the most relevant file_id or file_ids to query for the prompt: {prompt}. If the files seem irrelevant, return 'None'"
            )
            file_ids = re.findall(r"file-\w{24}", str(file_results))
            if file_ids:
                file_ids = list(set(file_ids))
                assistant = client.beta.assistants.create(
                    name="PDF Comprehender",
                    instructions="You are an expert technical writer.",
                    tools=[{"type": "retrieval"}],
                    model="gpt-4-turbo",
                    file_ids=file_ids,
                )
                thread = client.beta.threads.create()
                client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content="investigate and summarize for the prompt: " + prompt,
                )
                run = client.beta.threads.runs.create_and_poll(
                    thread_id=thread.id,
                    assistant_id=assistant.id,
                    instructions="you're an expert technical writer who can understand documents.",
                )
                if run.status == "completed":
                    messages = client.beta.threads.messages.list(thread_id=thread.id)
                    pdf_prompt = f"\n\n\nAfter examining the pdfs with the prompt {prompt}, the assistant also learned: {messages.data[0].content[0].text.value}\n\n\n"
        except Exception:
            import traceback

            print(traceback.format_exc())
    if before_selected_text or after_selected_text or selected_text:
        full_text = before_selected_text
        if selected_text:
            full_text += "\n\n <selected_text>\n\n"
            full_text += selected_text
            full_text += "\n\n </selected_text>\n\n"
        full_text += after_selected_text
        result = agent.invoke(
            f"Here is a document, and a section has been selected: \n\n<document>{full_text}</document>\n\n {pdf_prompt} Rewrite the selected text part of document. Respond with replacement or appended text for the selected text, which will be rendered as markdown, according to the user prompt \n<prompt>\n{prompt}\n</prompt>"
        )
    else:
        result = agent.invoke(
            prompt=f"Using all the previous information, {pdf_prompt} {prompt}"
        )
    if result.startswith("```markdown") and result.endswith("```"):
        result = result[11:-3]

    return result
