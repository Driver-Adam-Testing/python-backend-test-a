from collections.abc import Callable
from inspect import signature


class Tool:
    def __init__(
        self, function: Callable, description: str, enums: list[dict] | None = None
    ) -> None:
        self.description = description
        self.name = function.__name__
        self._function = function
        self.enums = enums if enums is not None else []

    @property
    def function(self):
        return self._function

    @function.setter
    def function(self, func: Callable):
        self._function = func

    def render_tool_for_prompt(self):
        return self.name + self.description

    def to_open_ai_dict(self):
        sig = signature(self._function)
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        name: {
                            "type": "string" if param.annotation is str else "string",
                            "description": name,
                        }
                        for name, param in sig.parameters.items()
                        if name != "agent_context"
                    },
                },
                "required": [
                    name
                    for name, param in sig.parameters.items()
                    if param.default is param.empty and name != "agent_context"
                ],
            },
        }
