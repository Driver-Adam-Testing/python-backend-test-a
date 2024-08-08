import re
from xml.etree import ElementTree as ET


def format_tool_prompt(tools):
    tool_descriptions = []
    for tool in tools:
        tool_description = f"""
        <tool_description>
        <tool_name>{tool.name}</tool_name>
        <description>{tool.description}</description>
        <parameters>
        """
        from inspect import signature

        sig = signature(tool.function)
        for name, param in sig.parameters.items():
            if name != "agent_context":
                tool_description += f"""
                <parameter>
                <name>{name}</name>
                <type>{'string' if param.annotation is str else 'string'}</type>
                <description>{name}</description>
                </parameter>
                """
        tool_description += """
        </parameters>
        </tool_description>
        """
        tool_descriptions.append(tool_description)

    CLAUDE_TOOL_PROMPT = f"""
    In this environment you have access to a set of tools you can use to answer the user's question.

    You may call them like this:
    <function_calls>
    <invoke>
    <tool_name>$TOOL_NAME</tool_name>
    <parameters>
    <$PARAMETER_NAME>$PARAMETER_VALUE</$PARAMETER_NAME>
    ...
    </parameters>
    </invoke>
    </function_calls>

    Here are the tools available:
    <tools>
    {''.join(tool_descriptions)}
    </tools>
    """
    return CLAUDE_TOOL_PROMPT


class Function:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class ToolCall:
    def __init__(self, function):
        self.function = function
        self.id = None


def parse_tool_calls_from_response(response):
    tool_calls = []
    xml_blocks = re.findall(
        r"<function_calls>.*?</function_calls>", response, re.DOTALL
    )
    for xml_block in xml_blocks:
        root = ET.fromstring(xml_block)
        function_calls = root.findall(".//invoke")
        for function_call in function_calls:
            tool_name = function_call.find("tool_name").text
            parameters = {
                param.tag: param.text
                for param in function_call.findall("./parameters/*")
            }
            function = Function(tool_name, parameters)
            tool_call = ToolCall(function)
            tool_calls.append(tool_call)
    return tool_calls


def format_tool_results(tool_names, args, results):
    formatted_results = ""
    for tool_name, arg, result in zip(tool_names, args, results, strict=False):
        formatted_results += f"""
        <result>
        <tool_name>{tool_name}</tool_name>
        <stdout>
        {arg}{result}
        </stdout>
        </result>
        """
    FORMAT_TOOL_RESULTS = f"""
    <function_results>
    {formatted_results}
    </function_results>
    """
    return FORMAT_TOOL_RESULTS
