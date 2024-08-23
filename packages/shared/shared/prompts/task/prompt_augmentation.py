PROMPT = """
Return only a rewritten version of the user prompt, with any necessary additional context.
The prompt should be the type of request that the user probably wants.
The user may want more or less detail. They may be altering or adding to a document.
Respond only with the prompt to be used by an llm to get better responses.
"""
MESSAGE = {"role": "system", "content": PROMPT}
