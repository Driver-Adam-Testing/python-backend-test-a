from openai import OpenAI


def query_file(file_id, query, assistant_id: str | None = None) -> str:
    client = OpenAI()
    if assistant_id is None:
        assistant = client.beta.assistants.create(
            name="File Searcher",
            instructions="You are an expert microprocessors and hardware engineer, as well as a brilliant technical writer.",
            model="gpt-4o",
            tools=[{"type": "file_search"}],
        )
        assistant_id = assistant.id

    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": query,
                "attachments": [
                    {"file_id": file_id, "tools": [{"type": "file_search"}]}
                ],
            }
        ]
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        instructions="You're an expert technical writer and engineer who can understand technical documents.",
        assistant_id=assistant_id,
    )

    if run.status == "completed":
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        summary = messages.data[0].content[0].text.value
        return summary
    raise Exception(f"Could not query file {file_id}")
