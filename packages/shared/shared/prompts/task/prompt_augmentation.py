PROMPT = """
Return a rewritten version of the user prompt, with any necessary additional context.
The user is attempting to understand their own code repositories, files, or understand technical documentation.
The prompt should be the type of request that the user probably wants.
The user may want more or less detail. They may be altering or adding to a document.
Respond with the prompt to be used by an llm to get better responses.
"""
MESSAGE = {"role": "system", "content": PROMPT}
