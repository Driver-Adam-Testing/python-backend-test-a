PROMPT_FIRST_ITERATION = """
Execute Tools.
This is the first iteration, and tools must be executed to retrieve initial context.
You have {remaining_iterations} more opportunities to execute tools.
"""
MESSAGE_FIRST_ITERATION = {"role": "user", "content": PROMPT_FIRST_ITERATION}

PROMPT_MIDDLE_ITERATION = """
If you have 100 percent confidence that there is no additional relevant context to be retrieved, return a response.
If you have not executed SearchTool, Execute SearchTool in hybrid mode.
If there is additional context required to become absolutely confident, Execute Tools.

You have {remaining_iterations} more opportunities to execute tools.
"""
MESSAGE_MIDDLE_ITERATION = {"role": "user", "content": PROMPT_MIDDLE_ITERATION}

PROMPT_FINAL_ITERATION = """
Return Response. This is the final iteration, and a response must be returned.
If writing code, ensure that the response uses only references to the source code results from the tools.
Ensure that any code or mermaid diagram is syntactically correct.
"""
MESSAGE_FINAL_ITERATION = {"role": "user", "content": PROMPT_FINAL_ITERATION}
