from modal import Function
from shared.v3.interfaces.llm_message import LlmMessage
from shared.v3.interfaces.llm_message_history import LlmMessageHistory
from shared.v3.interfaces.llm_response_type import LlmResponseType
from shared.v3.interfaces.llm_tool import LlmTool
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.llms.config.llm_config import LlmConfig

MODEL_ENTRYPOINT_FILE = "DeepSeek-R1-UD-IQ1_S/DeepSeek-R1-UD-IQ1_S-00001-of-00003.gguf"


class LlmModalDeepseekClient(LlmClient):
    def __init__(self, config: LlmConfig) -> None:
        super().__init__(config)

    def _generate(
        self,
        message_history: LlmMessageHistory,
        response_type: type[LlmResponseType] | None,
        tool_types: list[type[LlmTool]] | None,
    ) -> LlmMessage:
        deepseek_message_history = message_history.copy()
        if tool_types:
            for tool in tool_types:
                deepseek_message_history.add_message(
                    tool.to_parsing_description_message()
                )
        if response_type:
            deepseek_message_history.add_message(
                response_type.to_parsing_description_message()
            )
        # Optionally, trigger the model download if necessary.
        download_function = Function.from_name(
            "example-llama-cpp", "download_model", environment_name="neil"
        )

        download_function.remote(
            "unsloth/DeepSeek-R1-GGUF",
            ["*UD-IQ1_S*"],
            "02656f62d2aa9da4d3f0cdb34c341d30dd87c3b6",
        )

        # Get the inference function.
        modal_function = Function.from_name(
            "example-llama-cpp", "llama_cpp_inference", environment_name="neil"
        )
        extra_args = []
        if (
            hasattr(self.config, "context_window")
            and self.config.optimal_context_window
        ):
            extra_args.extend(["--ctx-size", str(self.config.optimal_context_window)])

        n_predict = 512

        result = modal_function.remote(
            MODEL_ENTRYPOINT_FILE,
            deepseek_message_history.to_string_prompt(),
            n_predict,
            extra_args,
        )
        return LlmMessage.from_string(result, response_type, tool_types)
