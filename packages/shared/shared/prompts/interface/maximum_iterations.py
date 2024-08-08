PROMPT = """You will have a maximum of {max_iterations} iterations to solve the user's problem"""


def render_prompt(max_iterations: int) -> str:
    return PROMPT.format(max_iterations=str(max_iterations))


def render_message(max_iterations: int) -> dict:
    return {"role": "system", "content": render_prompt(max_iterations=max_iterations)}
