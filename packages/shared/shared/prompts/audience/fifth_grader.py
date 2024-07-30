PROMPT = """
Curate the content for the following reader personae: The reader, a fifth grader, is interested in a simple and engaging explanation of how computers and software work. They want to see colorful illustrations showing the basic parts of a computer, simple diagrams explaining how software runs on these parts, and fun examples of what different programs can do. Additionally, the fifth grader would enjoy interactive elements or simple experiments that demonstrate basic concepts like coding, internet safety, and how software helps in everyday tasks.
"""

MESSAGE = {"role": "user", "content": PROMPT}

ASSISTANT_MESSAGE = {
    "role": "assistant",
    "content": "I will respond as I would to a fifth grader.",
}
