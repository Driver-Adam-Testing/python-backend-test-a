PROMPT = """Remove all speculation. If a text is speculative in it's entirety, remove it and admit you didn't have enough context to create non-speculative content. """

MESSAGE = {"role": "system", "content": PROMPT}


# TODO: Make this an inheritable tool class. Perhaps we add these things to agents? or create a util that appends system prompts and tools that allow content_errors?
def log_speculative_error(agent_context, error_message):
    if not hasattr(agent_context, "content_errors"):
        agent_context.content_errors = []
    agent_context.content_errors.append(error_message)
