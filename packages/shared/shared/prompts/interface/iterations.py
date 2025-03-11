PROMPT_FIRST_ITERATION = """
Execute Tools.
This is the first iteration, and tools must be executed to retrieve initial context.
You have {remaining_iterations} more opportunities to execute tools.
"""
MESSAGE_FIRST_ITERATION = {"role": "user", "content": PROMPT_FIRST_ITERATION}

PROMPT_MIDDLE_ITERATION = """
Review the source code in the files and write your answer using only the results from the tools.
If you have 100 percent confidence that there is no additional relevant context to be retrieved, you mayreturn a response.
If there are no SearchTool results in the history, you must Execute SearchTool in hybrid mode.
If there are only PDF results in the history, you must Execute SearchTool in hybrid mode.
You may not return a response if you do not have source code results from the tools.

You have {remaining_iterations} more opportunities to execute tools.
"""
MESSAGE_MIDDLE_ITERATION = {"role": "user", "content": PROMPT_MIDDLE_ITERATION}

PROMPT_FINAL_ITERATION = """
Return Response. This is the final iteration, and a response must be returned.
If writing code, ensure that the response uses only references to the source code results from the tools.
Ensure that any code or mermaid diagram is syntactically correct.
"""
MESSAGE_FINAL_ITERATION = {"role": "user", "content": PROMPT_FINAL_ITERATION}
