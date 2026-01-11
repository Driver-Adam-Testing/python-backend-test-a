import os

from openai import OpenAI

if os.environ.get("AZURE_OPENAI_BASE_URL"):
    base_url = os.environ["AZURE_OPENAI_BASE_URL"]
    base_url = f"https://{base_url}/openai/v1/"
    api_key = os.environ["AZURE_OPENAI_KEY_1"]
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )
else:
    client = OpenAI()


def query_file(file_id: str, query: str, assistant_id: str | None = None) -> str:
    if assistant_id is None:
        assistant = client.beta.assistants.create(
            name="Document Summarizer Assistant",
            instructions="You are an expert microprocessors and hardware engineer, as well as a brilliant technical writer and summarizer. You understand PDFs of all kinds.",
            model="gpt-4o",
            tools=[{"type": "file_search"}, {"type": "code_interpreter"}],
        )
        assistant_id = assistant.id

    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": query,
                "attachments": [
                    {"file_id": file_id, "tools": [{"type": "file_search"}]},
                    {"file_id": file_id, "tools": [{"type": "code_interpreter"}]},
                ],
            }
        ]
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        instructions="Summarize the key points of the document.",
        assistant_id=assistant_id,
    )

    if run.status == "completed":
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        summary = messages.data[0].content[0].text.value
        return summary
    raise Exception(f"Could not query file {file_id}")
