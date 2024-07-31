PROMPT = """Remove unnecessary language that is "in summary" or  "In conclusion". If sentences, paragraphs, or sections only reiterate or introduce information elsewhere in the text, Remove it.
"""

MESSAGE = {"role": "system", "content": PROMPT}
