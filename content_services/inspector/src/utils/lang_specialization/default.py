from .common import ListData
from utils.models import ChatOpenAI

SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT = """
You are a software engineering documentation expert. You write detailed documentation to explain software.

You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.
"""

SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT = """
You will be given the content of a source code file. In a single paragraph of 3 to 5 sentences, explain the purpose of the file. Consider questions such as the following when providing your output:

- Does this code provide narrow or broad functionality?
- Is this code a collection of many different components? If so, what is the common theme or purpose?
- What kind of code is this? For example, is this code clearly an executable (e.g., main.c), a header file, a library file intended to be imported elsewhere, a collection of configuration variables, etc.?
- Does it define public APIs or external interfaces?
"""

SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT = """
You will be given the content of a source code file. In a single paragraph of 3 to 5 sentences, explain the purpose of the file. Consider questions such as the following when providing your output:

- Does this code provide narrow or broad functionality?
- What kind of code is this? For example, is this code clearly an executable (e.g., main.c), a header file, a library file intended to be imported elsewhere, a collection of configuration variables, etc.?
"""

TECHNICAL_CONCEPTS = """
You will be given the content of a source code file. In a single paragraph of 3 to 5 sentences, describe the important technical features and their interactions in the file.

In writing your description, write about about the conceptual use cases, applications, logic, and component interactions instead of focusing on particular functions, variables, etc.
"""

IMPORTS_SYSTEM_PROMPT_JSON = """
Identify and list the imports and dependencies used in the code provided below.

You only respond with a list of imports and dependencies. **Always respond using exactly the following JSON schema**:
{
    "data": [
        <import1_name>,
        <import2_name>,
        ...
    ]
}

If there are no imports or dependencies return an empty array.
"""

IMPORTS_NONE_CONTENT = "\n---\nNo imports or dependencies defined in this file."


DATA_STRUCTURES_CHECKER_SYSTEM_PROMPT_JSON = """
Your job is to list any important data structures defined in the code provided below.

- A data structure is custom or compound type in a given programming language, such as structs, classes, or enums. Functions, methods, and variables are not data structures.
- An important data structure is a custom, complex, or compound data structure in the language of the provided code but does not include primitive types inherent to the programming language such as integers, floating point values, or strings.
- You are only looking for important data structures that are **fully defined** in the code given to you. That is, the implementation of the data structure is in the source code given to you. If a data structure is imported or used without being defined in the code, do not include it.

You only respond with a list of data structures. **Always respond using exactly the following JSON schema**:
{
    "data": [
        <name of first data structure>,
        <name of second data structure>,
        ...
    ]
}

If there are no data structures return an empty array.
"""

DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert programmer and a software engineering documentation expert. You write detailed documentation to explain code.

You focus on writing technical documentation for data structures. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a data structure to document and the source code where the data structure is defined.

Your job is to describe the data structure. **Always respond using exactly the following JSON schema**:
{
    "type": <type of the data structure>,
    "members": [
        {"name": <member_name1>, "content": <Terse 1 sentence description of the first member or field>},
        {"name": <member_name2>, "content": <Terse 1 sentence description of the second member or field>},
        ...
    ],
    "description": <one paragraph description of the data structure>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

DATA_STRUCTURES_FOUND_USER_PROMPT = """
Summarize the data structure in the code provided below.

- A data structure is custom or compound type in a given programming language, such as structs, classes, or enums. Functions, methods, and variables are not data structures.
- When describing an important data structure, provide detail that matches the complexity of the data structure. Large and complex data structures should get longer explanations, while small ones a single sentence.
"""

DATA_STRUCTURES_NONE_CONTENT = "\n---\nNo custom data structures defined in this file."

FUNCTIONS_CHECKER_SYSTEM_PROMPT_JSON = """
Your job is to list any functions defined in the code provided below.

- A function may be a free function or a method associated with a class, depending on the programming language.
- You are only looking for functions that are **fully defined and implemented** in the code given to you. That is, the implementation of the function is in the source code given to you. If a function is imported or used without being implemented in the code, do not include it.

You only respond with a list of functions. **Always respond using exactly the following JSON schema**:
{
    "data": [
        <name of first function>,
        <name of second function>,
        ...
    ]
}

If there are no functions return an empty array.
"""

FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert programmer and a software engineering documentation expert. You write detailed documentation to explain code.

You focus on writing technical documentation for functions. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a function to document and the source code where the function is defined.

Your job is to describe the function. **Always respond using exactly the following JSON schema**:
{
    "single_sentence": <terse single sentence description of the function>,
    "inputs": [
        {"name": <input_arg1>, "content": <description of input argument 1>},
        {"name": <input_arg2>, "content": <description of input argument 2>},
        ...
    ],
    "control_flow": [
        <bullet point 1 for description of control flow>,
        <bullet point 2 for description of control flow>,
        ...
    ],
    "output": <description of output>
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

FUNCTIONS_FOUND_USER_PROMPT = """
Summarize the function in the code provided below. Describe the inputs, control flow and logic, and output.

- When describing a function, provide detail that matches the complexity of the function body. Large and complex functions should get longer explanations, while small ones much less.
"""

FUNCTIONS_NONE_CONTENT = "\n---\nNo functions defined in this file."

VARIABLES_CHECKER_SYSTEM_PROMPT_JSON = """
Your job is to list any global variables defined in the code provided below.

- A global variable is declared at the top level scope. Local variables declared and used inside of functions or other scopes are not global variables. Only include global variables.
- You are only looking for global variables **defined** in the code given to you. If a variable is imported or used without being defined in the code, do not include it.

**You only include the name of any global variable**, not its value or contents.
You only respond with a list of global variable names. **Always respond using exactly the following JSON schema**:
{
    "data": [
        <name of first global variable>,
        <name of second global variable>,
        ...
    ]
}

If there are no global variables return an empty array.
"""

VARIABLES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert programmer and a software engineering documentation expert. You write detailed documentation to explain code.

You focus on writing technical documentation for variables. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a variable to document and the source code where the data structure is defined.

Your job is to describe the variable. **Always respond using exactly the following JSON schema**:
{
    "type": <type of the variable>,
    "description": <1 to 3 sentence description of the variable>,
    "use": <Terse 1 sentence description of how this variable is used>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

VARIABLES_FOUND_USER_PROMPT = """
Summarize the variable in the code provided below.

- A global variable is declared at the top level scope. Local variables declared and used inside of functions are not global variables. You will be describing a global variable.
- When describing a variable, provide detail that matches the complexity of the variable. Large and complex global variables (e.g., containing large struct instances) should get longer explanations, while small ones (e.g., one line definitions) much less.
"""

VARIABLES_NONE_CONTENT = "\n---\nNo global variables defined in this file."


def _default_checker(
    llm: ChatOpenAI,
    user_prompt: str,
    system_prompt: str,
    code: str,
    as_list_data_ds: bool = False,
) -> list[str] | ListData | None:
    list_data = ListData.from_llm(
        llm=llm, system_prompt=system_prompt, user_prompt=user_prompt, code=code
    )
    if len(list_data.data) > 0:
        if as_list_data_ds:
            return list_data
        else:
            return list_data.data
    else:
        return None


def default_imports_checker(llm: ChatOpenAI, code: str) -> ListData | None:
    return _default_checker(
        llm=llm,
        user_prompt="",
        system_prompt=IMPORTS_SYSTEM_PROMPT_JSON,
        code=code,
        as_list_data_ds=True,
    )


def default_variable_checker(llm: ChatOpenAI, code: str) -> list[str] | None:
    return _default_checker(
        llm=llm,
        user_prompt="",
        system_prompt=VARIABLES_CHECKER_SYSTEM_PROMPT_JSON,
        code=code,
    )


def default_data_structure_checker(llm: ChatOpenAI, code: str) -> list[str] | None:
    return _default_checker(
        llm=llm,
        user_prompt="",
        system_prompt=DATA_STRUCTURES_CHECKER_SYSTEM_PROMPT_JSON,
        code=code,
    )


def default_function_checker(llm: ChatOpenAI, code: str) -> list[str] | None:
    return _default_checker(
        llm=llm,
        user_prompt="",
        system_prompt=FUNCTIONS_CHECKER_SYSTEM_PROMPT_JSON,
        code=code,
    )
