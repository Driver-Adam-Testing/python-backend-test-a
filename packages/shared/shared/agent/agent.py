import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic
import requests
from openai import OpenAI
from openai.types.chat.chat_completion_message import ChatCompletionMessage

from shared.agent.models.claude import claude_tool_formatter
from shared.agent.vector_db import VectorDb
from shared.utils.bcolors import bcolors

SUPPORTED_MODELS = [
    {"model": "gpt-4-turbo-preview", "provider": "openai"},
    {"model": "gpt-4-turbo", "provider": "openai"},
    {"model": "gpt-4o", "provider": "openai"},
    {"model": "claude-3-opus-20240229", "provider": "anthropic"},
    {"model": "claude-3-haiku-20240307", "provider": "anthropic"},
    {"model": "claude-3-sonnet-20240229", "provider": "anthropic"},
]


class AgentBase:
    def __init__(
        self,
        workspace_id: str,
        codebase_id: str = None,
        model: str = "gpt-4-turbo-preview",
        max_iterations: int = 1,
        tools=None,
        id: uuid.UUID = None,
    ):
        self.iterations = 0
        self.max_iterations = max_iterations
        self.workspace_id = workspace_id
        self.codebase_id = codebase_id
        self.max_iterations = max_iterations
        self.tools = tools if tools is not None else []
        self.model = model
        self.collection = VectorDb(workspace_id=workspace_id)
        self.messages = []
        if id is None:
            self.id = self.collection.log_agent(self.codebase_id, self.model)
        else:
            self.id = id
        self._backend_token = None

    @property
    def backend_token(self):
        if self._backend_token is None:
            # TODO: get this from settings
            auth0_domain = os.getenv("AUTH0_DOMAIN")
            client_id = os.getenv("AUTH0_CLIENT_ID")
            client_secret = os.getenv("AUTH0_CLIENT_SECRET")
            audience = os.getenv("AUTH0_AUDIENCE")

            token_url = f"https://{auth0_domain}/oauth/token"
            payload = {
                "client_id": client_id,
                "client_secret": client_secret,
                "audience": audience,
                "grant_type": "client_credentials",
            }
            headers = {"content-type": "application/json"}

            response = requests.post(token_url, json=payload, headers=headers)
            if response.status_code == 200:
                self._backend_token = response.json().get("access_token")
            else:
                raise Exception(f"Failed to obtain access token: {response.text}")
        return self._backend_token

    def _print_message(self, message: ChatCompletionMessage | dict[str, str]):
        try:
            if isinstance(message, ChatCompletionMessage):
                print(
                    bcolors.FAIL,
                    message.role,
                    bcolors.WARNING,
                    message.content,
                    bcolors.ENDC,
                )
            else:
                print(
                    bcolors.FAIL,
                    message["role"],
                    bcolors.WARNING,
                    message["content"],
                    message.get("tool_call_id", ""),
                    message.get("name", ""),
                    bcolors.ENDC,
                )
        except KeyError as e:
            print(f"Warning: Message is incorrectly formatted. Missing key: {e}")

    def add_message(
        self,
        message: ChatCompletionMessage | dict[str, str] | str,
        log: bool = True,
    ):
        if isinstance(message, ChatCompletionMessage):
            self.messages.append(message)
        elif isinstance(message, str):
            message = {"role": "user", "content": message}
        else:
            self.messages.append(message)
        self._print_message(message)
        if log and self.id is not None:
            if isinstance(message, ChatCompletionMessage):
                self.collection.log_agent_message(self.id, message.model_dump())
            else:
                self.collection.log_agent_message(self.id, message)

    def _execute_tool_call(self, tool_call):
        # TODO: there's probably a better  hierarchical version of determining whether the tool was correctly called.
        function_id = getattr(tool_call, "id", None)
        if not hasattr(tool_call, "function"):
            return (
                "Error: 'tool_call' does not have 'function' attribute.",
                function_id,
                None,
            )
        function_name = getattr(tool_call.function, "name", None)
        function_arguments = getattr(tool_call.function, "arguments", None)

        if not function_name or not function_arguments or not function_id:
            return (
                "Error: Invalid tool call structure. Expected 'name', 'arguments', and 'id'.",
                function_id,
                function_name,
            )

        try:
            function = next(
                tool.function for tool in self.tools if tool.name == function_name
            )
            print(
                bcolors.OKBLUE,
                function_name,
                bcolors.OKCYAN,
                function_arguments,
                bcolors.ENDC,
            )

            if isinstance(function_arguments, str):
                function_args = json.loads(function_arguments)
            elif isinstance(function_arguments, dict):
                function_args = function_arguments
            else:
                raise TypeError("Arguments must be either a string or a dictionary.")
            if "agent_context" in function.__code__.co_varnames:
                if function_args is None:
                    function_args = {}
                function_args["agent_context"] = self
            return (function(**function_args), function_id, function_name)
        except Exception as e:
            return (f"Error: {str(e)}", function_id, function_name)

    def _iterate(self):
        self.iterations += 1
        if self.max_iterations > 1:
            self.add_message(
                {
                    "role": "user",
                    "content": f"There are {self.max_iterations - self.iterations} remaining AI agent iterations remaining to solve the problem.",
                }
            )

    def invoke(self, prompt: str):
        self.iterations = 0
        self.add_message({"role": "user", "content": prompt})
        while self._iterate():
            if self.iterations > self.max_iterations:
                break
        try:
            return self.messages[-1].content
        except Exception:
            return self.messages[-1]["content"]


class OpenAIAgent(AgentBase):
    def __init__(
        self,
        workspace_id: str,
        codebase_id: str = None,
        model: str = "gpt-4-turbo-preview",
        max_iterations: int = 1,
        tools=None,
        id=None,
    ):
        super().__init__(workspace_id, codebase_id, model, max_iterations, tools, id)
        self.client = OpenAI()

    @property
    def _tool_list(self):
        return [tool.__open_ai_dict__() for tool in self.tools]

    def _execute_tool_calls(self, tool_calls):
        """
        OpenAI expects all tool calls to return in a several tool messages with tool_call_id.
        """
        if not tool_calls:
            return
        futures = []

        with ThreadPoolExecutor() as executor:
            messages = []
            for tool_call in tool_calls:
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_call.function.name,
                        "content": "Error in tool call",
                    }
                )
                future = executor.submit(self._execute_tool_call, tool_call)
                futures.append(future)

            for future in as_completed(futures):
                try:
                    function_response, tool_call_id, _ = future.result()
                    if function_response:
                        for message in messages:
                            if message["tool_call_id"] == tool_call_id:
                                message["content"] = function_response
                                break
                except Exception:
                    pass
            for message in messages:
                self.add_message(message)

    def _create_completion(self):
        if self.tools:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self._tool_list,
                tool_choice="auto",
            )
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
            )
        return response

    def _iterate(self):
        super()._iterate()
        response = self._create_completion()
        self.add_message(response.choices[0].message)
        if response.choices[0].message.tool_calls:
            self._execute_tool_calls(response.choices[0].message.tool_calls)
            return True
        else:
            return False

    def invoke(self, prompt: str):
        return super().invoke(prompt)


class AnthropicAgent(AgentBase):
    def __init__(
        self,
        workspace_id: str,
        codebase_id: str = None,
        model: str = "gpt-4-turbo-preview",
        max_iterations: int = 1,
        tools=None,
        id=None,
    ):
        super().__init__(workspace_id, codebase_id, model, max_iterations, tools, id)
        self.client = anthropic.Anthropic()

    def _execute_tool_calls(self, tool_calls):
        """
        Anthropic expects all tool calls to return in a single user message.
        """
        if not tool_calls:
            return
        futures = []

        with ThreadPoolExecutor() as executor:
            for tool_call in tool_calls:
                future = executor.submit(self._execute_tool_call, tool_call)
                futures.append(future)

            tool_names = []
            tool_call_ids = []
            function_responses = []

            for future in as_completed(futures):
                function_response, tool_call_id, function_name = future.result()
                tool_names.append(function_name)
                tool_call_ids.append(tool_call_id)
                function_responses.append(function_response)

            formatted_tool_results = claude_tool_formatter.format_tool_results(
                tool_names, tool_call_ids, function_responses
            )
            self.add_message(
                {
                    "role": "user",
                    "content": formatted_tool_results,
                }
            )

    def _create_completion(self):
        """
        Anthropic only takes a single system prompt, so aggregate all of them.
        """
        system_messages = [
            message["content"]
            for message in self.messages
            if message["role"] == "system"
        ]
        system_string = " ".join(system_messages)
        filtered_messages = [
            message
            for message in self.messages
            if message["role"] in ["user", "assistant"]
        ]
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_string,
            messages=filtered_messages,
        )
        return response

    def _iterate(self):
        super()._iterate()
        user_messages = []
        for message in reversed(self.messages):
            if message["role"] == "user":
                user_messages.append(message["content"])
                self.messages.pop()
            else:
                break
        merged_user_message = " ".join(user_messages)
        self.messages.append({"role": "user", "content": merged_user_message})
        response = self._create_completion()
        self.add_message({"role": "assistant", "content": response.content[0].text})
        tool_calls = claude_tool_formatter.parse_tool_calls_from_response(
            response.content[0].text
        )
        if tool_calls:
            self._execute_tool_calls(tool_calls)
            return True
        else:
            return False

    def invoke(self, prompt: str):
        if self.iterations == 0 and self.tools:
            self.add_message(
                {
                    "role": "system",
                    "content": claude_tool_formatter.format_tool_prompt(self.tools),
                }
            )
        return super().invoke(prompt)


class Agent:
    def __init__(
        self,
        workspace_id: str,
        codebase_id: str = None,
        model: str = "gpt-4-turbo-preview",
        max_iterations: int = 1,
        tools=None,
    ):
        self.model_provider = next(
            (item["provider"] for item in SUPPORTED_MODELS if item["model"] == model),
            None,
        )
        if self.model_provider is None:
            raise ValueError(f"Model {model} is not supported.")
        if self.model_provider == "openai":
            self.agent = OpenAIAgent(
                workspace_id, codebase_id, model, max_iterations, tools
            )
        elif self.model_provider == "anthropic":
            self.agent = AnthropicAgent(
                workspace_id, codebase_id, model, max_iterations, tools
            )
        else:
            raise ValueError(f"Provider {self.model_provider} is not supported.")

    def add_message(self, message, log=True):
        self.agent.add_message(message, log=log)

    def invoke(self, prompt):
        return self.agent.invoke(prompt)


def get_agent(self, agent_instance_id: str):
    (
        agent_instance,
        agent_messages,
        agent_errors,
        chunk_texts,
    ) = self.collection.get_agent_instance(agent_instance_id)
    if agent_instance is None:
        return None
    agent = Agent(
        workspace_id=agent_instance.workspace_id,
        codebase_id=agent_instance.codebase_id,
        model=agent_instance.model,
        id=agent_instance.id,
    )
    for message in agent_messages:
        agent.add_message(message)
    return agent
