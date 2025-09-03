from shared.v3.globals.glossary import DATA_SOURCES
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.utils.datasource import DataSource


class DataSourceMessage(LlmMessage):
    """
    Describe the DataSource structure from datasource.py for tools to use.
    """

    @classmethod
    def from_context(cls, datasource: DataSource) -> "DataSourceMessage":
        """
        Build a DataSourceMessage that includes human-readable information about
        the provided DataSource for iteration-based usage.
        """

        content = f"{DATA_SOURCES.description}\n{DATA_SOURCES.wrap(datasource.describe_contents_char_limit(char_limit=10000))}"
        return cls(message_kind=MessageKind.DEVELOPER, content=content)


class DataSourceSystemMessage(LlmMessage):
    """
    A system message that provides an expanded description of the DataSource class defined in datasource.py.
    """

    message_kind: MessageKind = MessageKind.DEVELOPER
    content: str = (
        "Tools retrieve references only from the paths defined in the DataSource. "
        "The DataSource class acts as a curated collection of references to relevant files, directories, "
        "and other organizational resources, while caching the associated Node objects for efficient access. "
        "Restricting Tools to these curated paths ensures they stay focused on pertinent information and avoid irrelevant content. "
        "By consolidating these references, the DataSource simplifies how Tools find and use documentation, source code, "
        "and other materials for a given organization. "
        "This information is strictly for guiding Tools in determining whether enough context is provided to respond to the user. "
        "Do not disclose any system knowledge of the DataSource to users; it is intended solely for the Tools' internal use."
    )


class DataSourceTuningSystemMessage(LlmMessage):
    """
    A system message that provides an expanded description of the DataSource class defined in datasource.py.

    """

    message_kind: MessageKind = MessageKind.DEVELOPER
    content: str = (
        "DataSources can be 'tuned'. A tuned datasource has more specific paths to relevant files, and directories. "
        "It represents a subset of the codebase that can include a selection of directories to search through."
        "Well tuned DataSources will have a higher precision for the queries they are used in."
        "A Tuned datasource is a list of nodes and their descendants. "
        "In order to tune a datasource, a user can click on the tuning icon on the codebase in the sources view, and select and deselect their desired files and directories to include in the datasource."
        "Good tuning will reduce irrelevant or distracting results in internal searches, improving the quality of the systems documentation generation."
    )
