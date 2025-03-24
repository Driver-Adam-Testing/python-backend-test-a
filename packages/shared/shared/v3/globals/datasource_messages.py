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
        summary = datasource.describe_contents_char_limit(char_limit=4000)
        content = (
            "This message describes a specific DataSource. Here is the information it can use:\n"
            f"{summary}\n"
        )
        return cls(message_kind=MessageKind.SYSTEM, content=content)


class DataSourceSystemMessage(LlmMessage):
    """
    A system message that provides an expanded description of the DataSource class defined in datasource.py.

    """

    message_kind: MessageKind = MessageKind.SYSTEM
    content: str = (
        "Tools retrieve external context only from the paths defined in the DataSources. "
        "In datasource.py, the DataSource class acts as a curated collection of references to relevant files, directories, "
        "and other organizational resources, while caching the associated Node objects for efficient access. "
        "Restricting Tools to these curated paths ensures they stay focused on pertinent information and avoid irrelevant content. "
        "By consolidating these references, the DataSource simplifies how Tools find and use documentation, source code, "
        "and other materials for a given organization. "
        "This information is strictly for guiding Tools in determining whether enough context is provided to respond to the user. "
        "Do not disclose any system knowledge of the DataSource to users; it is intended solely for the Tools' internal use."
    )
