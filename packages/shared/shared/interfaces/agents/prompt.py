from pydantic import BaseModel


class PromptWithContext(BaseModel):
    """
    User prompt with additional context.

    Attributes:
        prompt (str): The user prompt.
        context (T): Generic type for context information.
    """

    prompt: str | None = None
    context: object | None = None

    def __init__(self, prompt: str, **kwargs):
        super().__init__(**kwargs)
        self.prompt = prompt

    def create_user_prompt(self) -> str:
        """
        Create a user prompt with context in XML format.

        Returns:
            str: The user prompt with context in XML format.
        """

        def dict_to_xml(d: dict) -> str:
            """
            Convert a dictionary to an XML string.

            Args:
                d (dict): The dictionary to convert.

            Returns:
                str: The XML string representation of the dictionary.
            """
            xml = ""
            for key, value in d.items():
                if isinstance(value, dict):
                    xml += f"<{key}>{dict_to_xml(value)}</{key}>"
                else:
                    xml += f"<{key}>{value}</{key}>"
            return xml

        def list_to_xml(lst: list) -> str:
            """
            Convert a list to an XML string.

            Args:
                lst (list): The list to convert.

            Returns:
                str: The XML string representation of the list.
            """
            xml = ""
            for item in lst:
                xml += f"<list_item>{object_to_xml(item)}</list_item>"
            return xml

        def object_to_xml(obj) -> str:
            """
            Convert an object to an XML string by converting its __dict__ attribute or using model_dump if available.

            Args:
                obj (T): The object to convert.

            Returns:
                str: The XML string representation of the object.
            """
            if isinstance(obj, dict):
                return dict_to_xml(obj)
            elif isinstance(obj, list):
                return list_to_xml(obj)
            elif hasattr(obj, "model_dump"):
                return dict_to_xml(obj.model_dump())
            elif hasattr(obj, "__dict__"):
                return dict_to_xml(obj.__dict__)
            else:
                return str(obj)

        context_xml = ""
        if self.context:
            context_xml += "<context>"
            context_xml += object_to_xml(self.context)
            context_xml += "</context>"
            user_prompt = f"<prompt>{self.prompt}</prompt>{context_xml}"
        else:
            user_prompt = self.prompt

        return user_prompt

    def __str__(self) -> str:
        return self.create_user_prompt()
