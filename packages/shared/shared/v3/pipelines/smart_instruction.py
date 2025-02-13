from shared.interfaces.agents.data_scope import DataScope
from shared.v3.messages.llm_message import LlmMessage
from shared.v3.messages.llm_message_kind import MessageKind
from shared.v3.pipelines.abbreviate_page_content import (
    AbbreviatedPageContentPipelineResponse,
    abbreviate_page_content,
)
from shared.v3.pipelines.get_information_set_definitions import (
    RetrievalSets,
    get_information_set_definitions,
)
from shared.v3.pipelines.interfaces.pipeline_request import PipelineExecutionRequest


class SmartInstructionUserMessage(LlmMessage):
    @classmethod
    def from_context(
        cls,
        prompt: str,
        before: str,
        after: str,
        instruction: str | None = None,
        query_params: list[str] | None = None,
    ) -> "SmartInstructionUserMessage":
        content = f"""
        User prompt: {prompt}

        Context before instruction:
        {before}

        Context after instruction:
        {after}

        {"Instruction: " + instruction if instruction else ""}
        {"Query parameters: "+  ', '.join(query_params) if query_params else ""}
        """
        return cls(message_kind=MessageKind.USER, content=content.strip())


def run_smart_instruction(
    user_prompt: str,
    text_before_instruction: str,
    text_after_instruction: str,
    datascope: DataScope,
) -> dict:
    import time

    start_time = time.time()

    abbreviated_page_content: AbbreviatedPageContentPipelineResponse = (
        abbreviate_page_content(
            pipeline_execution_request=PipelineExecutionRequest(
                original_prompt=user_prompt,
                text_before_selection=text_before_instruction,
                text_after_selection=text_after_instruction,
                selected_text=None,
                datascope=datascope,
            )
        )
    )

    end_time = time.time()
    print(f"Abbreviate page content execution time: {end_time - start_time} seconds")
    print("abbreviated_page_content", abbreviated_page_content)

    # TODO: do we want to execute this in parallel
    retrieval_instructions: RetrievalSets = get_information_set_definitions(
        pipeline_execution_request=PipelineExecutionRequest(
            original_prompt=user_prompt,
            text_before_selection=abbreviated_page_content.abbreviated_before
            if abbreviated_page_content.abbreviated_before
            else None,
            text_after_selection=abbreviated_page_content.abbreviated_after
            if abbreviated_page_content.abbreviated_after
            else None,
            selected_text=None,
            datascope=datascope,
        )
    )

    # all_information_sets = []

    # for information_set in retrieval_instructions.information_sets:
    #     agent = BaseAgent(
    #         datascope=datascope,
    #         config=LlmConfig.from_name("gpt_4o_mini"),
    #         tools=[HybridSearchTool],
    #         message_history=LlmMessageHistory(
    #             messages=[
    #                 AgenticContextMessage(),
    #                 DriverApplicationMessage(),
    #                 SmartInstructionUserMessage.from_context(
    #                     prompt=user_prompt,
    #                     before=text_before_instruction,
    #                     after=text_after_instruction,
    #                     instruction=information_set.retrieval_instructions,
    #                     query_params=information_set.query_strings,
    #                 ),
    #             ]
    #         ),
    #     )

    #     response = agent.invoke(iterations=2)
    #     all_information_sets.append(response.content)
    # print(all_information_sets)
    # final_response = LlmClient.from_config(LlmConfig.from_name("gpt_4o_mini")).generate(
    #     message_history=LlmMessageHistory(
    #         messages=[
    #             DriverApplicationMessage(),
    #             LlmMessage(
    #                 message_kind=MessageKind.DEVELOPER,
    #                 content="\n".join(all_information_sets),
    #             ),
    #             SmartInstructionUserMessage.from_context(
    #                 prompt=user_prompt,
    #                 before=text_before_instruction,
    #                 after=text_after_instruction,
    #             ),
    #         ]
    #     ),
    # )

    return {
        "abbreviated_before": abbreviated_page_content.abbreviated_before
        if abbreviated_page_content.abbreviated_before
        else "",
        "abbreviated_after": abbreviated_page_content.abbreviated_after
        if abbreviated_page_content.abbreviated_after
        else "",
        "final_response": abbreviated_page_content,
    }
