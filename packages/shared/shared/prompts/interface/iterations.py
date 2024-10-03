PROMPT_FIRST_ITERATION = """
Execute Tools.
This is the first iteration, and tools must be executed to retrieve initial context.
You have {remaining_iterations} more opportunities to execute tools.
"""
MESSAGE_FIRST_ITERATION = {"role": "user", "content": PROMPT_FIRST_ITERATION}

PROMPT_MIDDLE_ITERATION = """
Return a Response ONLY if you have above 90 percent confidence that you have been as specific and comprehensive as possible in your response.
If there is additional context required to become absolutely confident, Execute Tools.
If you haven't executed every kind of tool, Execute Tools.
If there may be additional relevant context, Execute Tools.

You have {remaining_iterations} more opportunities to execute tools.
"""
MESSAGE_MIDDLE_ITERATION = {"role": "user", "content": PROMPT_MIDDLE_ITERATION}

PROMPT_FINAL_ITERATION = """
Return Response. This is the final iteration, and a response must be returned.
"""
MESSAGE_FINAL_ITERATION = {"role": "user", "content": PROMPT_FINAL_ITERATION}
