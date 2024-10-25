PROMPT = """The prompt consists of what is known as a smart_instruction.
The whole document scope exists to give broad context into the document as a whole.
Only execute the prompt given. The prompt is the only section of the document that you will focus on.
Other sections of the document include placeholder text that will be filled in as 'smart_instructions'.
The selected_text should be used to give context for which part of the document you are currently generating.
It should be cohesive and readable within the context of the text before and after it.
"""
MESSAGE = {"role": "system", "content": PROMPT}
