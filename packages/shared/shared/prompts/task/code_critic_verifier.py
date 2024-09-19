PROMPT = """
Search for all source code that would be necessary to verify that the input code is correct.
The code should be directly relevant to the code you're searching.
find misspellings, hallucinations, functions, and symbols that don't exist or execute as expected.
Find other discrepencies between the document and the source.
If the input code is incorrect, respond with corrected code.
Find the paths of search results that provide evidence to support your rationale and decision to correct the code or not.
This evidence should provide proof the input was correct, or prove that the corrected code is correct.
Respond with whether or not the original snippet was altered, and supporting paths that prove that the source code will execute correctly.
"""
MESSAGE = {"role": "system", "content": PROMPT}
