from shared.tool_executors import ToolUseError, get_llm_onboarding_guide
from shared.v3.globals.glossary import (
    TOOL_ERROR_MESSAGE,
    TOOL_RESPONSE_CONTENT_MARKDOWN,
)
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.interfaces.llm_tool import LlmTool
from shared.v3.utils.references import Reference


class LlmOnboardingGuideTool(LlmTool):
    """
    LlмOnboardingGuideTool returns a complete LLM onboarding guide document for
    the specified codebase in markdown format.

    This tool provides a comprehensive onboarding guide optimized to help LLM
    agents quickly understand and navigate a codebase. The guide includes
    high-signal directories, critical files, start-here recommendations, and
    navigation tips with cross-references to help agents efficiently work with
    the codebase structure and key components.

    Attributes
    ----------
    codebase_name: str
        The name of the codebase to get an LLM onboarding guide for. Must be a
        valid codebase name that exists in the system.
    """

    codebase_name: str

    def _execute(self) -> None:
        try:
            llm_onboarding_guide = get_llm_onboarding_guide(
                self.datasource.organization_id, self.codebase_name
            )
        except ToolUseError as e:
            self._error_message = e.agent_message
            return

        ref = Reference(
            content=llm_onboarding_guide,
            tool_call_id=self.tool_call_id,
            metadata={
                "codebase_name": self.codebase_name,
            },
        )
        self._references.add_reference(ref)

    def to_tool_call_response_message(self) -> LlmMessage:
        if not self._references:
            return LlmMessage(
                message_kind=MessageKind.TOOL_CALL_RESPONSE,
                content=TOOL_ERROR_MESSAGE.wrap(self._error_message),
                tool_response=LlmMessage.ToolCallResponse(
                    id=self.tool_call_id or None, name=self.__class__.__name__
                ),
            )

        return LlmMessage(
            message_kind=MessageKind.TOOL_CALL_RESPONSE,
            content=(
                f"{self.__class__.__name__} results for {self.codebase_name}:\n"
                f"{TOOL_RESPONSE_CONTENT_MARKDOWN.wrap(next(iter(self._references)).content)}"
            ),
            tool_response=LlmMessage.ToolCallResponse(
                id=self.tool_call_id or None, name=self.__class__.__name__
            ),
        )

    @property
    def status(self) -> str:
        if self._error_message:
            return f"{self.__class__.__name__} failed"
        if self._references:
            return f"Executed {self.__class__.__name__}:\n\tcodebase_name={self.codebase_name}"
        return ""
