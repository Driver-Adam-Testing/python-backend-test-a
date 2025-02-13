from shared.v3.messages.llm_message import LlmMessage, MessageKind


class DriverApplicationMessage(LlmMessage):
    message_kind: MessageKind = MessageKind.SYSTEM
    content: str = (
        "This request is part of a documentation generation system. The system is designed to assist in creating various forms of technical documentation, "
        "including architectural diagrams, tables, lists, code snippets, and technical documents. The goal is to streamline the process of generating "
        "comprehensive and accurate documentation for different aspects of user-uploaded codebases and their associated technical documentation for hardware and software."
        "All requests will ultimately be rendered as markdown in an application. All requests will be in reference to some number of files, directories, or other technical documentation."
    )


class AgenticContextMessage(LlmMessage):
    message_kind: MessageKind = MessageKind.SYSTEM
    content: str = (
        "This message is part of a larger system of interconnected LLMs. As an LLM, I may be tasked with retrieving information, preparing information for other LLMs to consume, or composing user responses. "
        "The system is designed to work collaboratively, ensuring that each LLM contributes to the overall goal of generating comprehensive and accurate technical documentation. "
        "By leveraging the strengths of multiple LLMs, the system can efficiently handle complex requests and provide high-quality outputs for various documentation needs."
    )
