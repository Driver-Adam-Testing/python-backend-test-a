# Prompt Strings
IMPORTANT = "!IMPORTANT!"
PARSEABLE_CLASS_NAME = "parseable_class_name"

FORMAT_RESPONSE_AS_JSON_f_class_name__example_json__docstring = (
    "Format your response as a JSON object that can be parsed into a {class_name}(pydantic.BaseModel) instance.\n"
    + "{docstring}\n"
    + IMPORTANT
    + " Set the "
    + PARSEABLE_CLASS_NAME
    + " field to '{class_name}'"
    + "\nHere is an example of the JSON object's schema:\n{example_json}"
)

FORMAT_TOOL_CALL_REQUEST_f_class_name__example_json__docstring = (
    "Format your tool call request as a JSON object, that can be parsed into a {class_name}(pydantic.BaseModel) instance.\n"
    + "{docstring}\n"
    + IMPORTANT
    + " Set the "
    + PARSEABLE_CLASS_NAME
    + " field to '{class_name}'"
    + "\nHere is an example of the JSON object's schema:\n{example_json}"
)


PARSEABLE_EXAMPLE_INT = 123
PARSEABLE_EXAMPLE_FLOAT = 3.14
PARSEABLE_EXAMPLE_BOOL = True
PARSEABLE_EXAMPLE_STR = "example_string"
PARSEABLE_EXAMPLE_DOCSTRING_KEY = "_docstring"
