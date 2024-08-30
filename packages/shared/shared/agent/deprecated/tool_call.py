import json


class ToolCall:
    id: str
    name: str
    args: dict
    response: any = None

    @classmethod
    def from_openai_tool_call(cls, tool_call):
        cls.id = getattr(tool_call, "id", None)
        cls.name = getattr(tool_call.function, "name", None)
        args = getattr(tool_call.function, "arguments", None)
        if args is None:
            args = {}
        if isinstance(args, str):
            cls.args = json.loads(args)
        elif isinstance(args, dict):
            cls.args = args
        else:
            raise TypeError("Arguments must be either a string or a dictionary.")
        return cls
