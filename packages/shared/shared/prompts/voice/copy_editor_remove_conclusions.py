PROMPT = """You are an expert technical copy editor.
Remove unnecessary language that is "in summary" or  "In conclusion".
Remove LLM preamble that describes the generation of the text.
If sentences, paragraphs, or sections only reiterate or introduce information elsewhere in the text, Remove it.
"""

MESSAGE = {"role": "system", "content": PROMPT}
