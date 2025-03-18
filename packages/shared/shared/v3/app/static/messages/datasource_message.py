from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.utils.datasource import DataSource


class DataSourceMessage(LlmMessage):
    """
    Describe the DataSource structure from datasource.py for tools to use.
    """

    message_kind: MessageKind = MessageKind.SYSTEM

    @classmethod
    def from_context(cls, datasource: DataSource) -> "DataSourceMessage":
        """
        Build a DataSourceMessage that includes human-readable information about
        the provided DataSource for iteration-based usage.
        """
        summary = datasource.human_readable_summary()
        content = (
            "This message describes a specific DataSource and the sources it can use:\n"
            f"{summary}\n"
            "All information references will be sourced from within the paths of the files and folders within these paths above."
        )
        return cls(message_kind=MessageKind.SYSTEM, content=content)
