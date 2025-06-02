# Purpose
The provided Python code defines a class `CodebaseFolderSummaryTool`, which is a specialized tool designed to summarize the content of a codebase folder at a specified directory path. This class inherits from `ToolStrict`, indicating that it is part of a framework or system that enforces strict tool behavior. The primary functionality of this tool is to interact with a database to retrieve and summarize long descriptions of codebase content, specifically targeting folders or codebases that serve as the root of a project. The tool is intended to be used when there is no prior search history available, providing a summarized context of the codebase's structure and content.

The `execute` method is the core component of this class, where it establishes a session with the database to perform a query that joins `DerivedContent` and `Node` models. It filters the results to include only those with specific content kinds, such as long descriptions. The method then formats the retrieved content into XML-like strings and creates `SearchResult` objects, which are aggregated into `SearchResults` and added to an agent's search results. This tool is part of a larger system, as indicated by its interaction with an `AgentBase` and the use of shared interfaces and models, suggesting it is designed to be integrated into a broader application or framework for codebase analysis and management.
# Imports and Dependencies

---
- `database.db`
- `database.models_v1`
- `database.models_v2`
- `sqlmodel`
- `shared.agent.agent_base`
- `shared.agent.tools.tool_strict`
- `shared.interfaces.search`


# Classes

---
### CodebaseFolderSummaryTool 
- **Type**: `class`
- **Members**:
    - `codebase_directory_path`: The path to the directory.
- **Description**: The CodebaseFolderSummaryTool class is designed to summarize the content of a codebase folder located at a specified directory path. It is particularly useful for gaining a summarized context of an entire folder or codebase, especially when the folder is the root of the codebase. The class includes an execute method that interacts with a database to retrieve and format content descriptions, which are then added to an agent's search results. Additionally, it provides a class method system_prompt to guide its usage in certain scenarios.
- **Inherits From**:
    - ToolStrict

**Methods**

---
#### CodebaseFolderSummaryTool.execute
The `execute` function retrieves and formats long description content from a database for a specified codebase directory path and adds the results to an agent.
- **Inputs**:
    - `agent`: An instance of AgentBase, which provides the scope and receives the search results.
- **Control Flow**:
    - The function begins by creating a child data scope for the agent using the codebase directory path.
    - A database session is initiated using `get_session()`.
    - A SQL query is constructed to select `DerivedContent` entries joined with `Node` where the node ID matches the first node ID in the scope and the content kind is either `LONG_DESCRIPTION` or `TOP_LEVEL_LONG_DESCRIPTION`.
    - The query is executed, and all matching rows are fetched into `derived_contents`.
    - If no content is found, a message indicating no content is returned.
    - For each content in `derived_contents`, a formatted XML-like string is created and added to `formatted_results`.
    - A `SearchResult` object is created for each content and added to `search_results`.
    - The aggregated search results are added to the agent using `add_search_results`.
    - Finally, the function returns a string of joined formatted results.
- **Output**:
    - A string containing formatted results of long description content, or a message indicating no content was found.


---
#### CodebaseFolderSummaryTool.system_prompt
The `system_prompt` function provides a directive for using the `CodebaseFolderSummaryTool` when top or second level codebase folders are present in searchable paths.
- **Inputs**:
    - None
- **Control Flow**:
    - The function is a class method, indicated by the `@classmethod` decorator, which means it is called on the class itself rather than an instance of the class.
    - The function returns a static string message that serves as a prompt or instruction.
- **Output**:
    - A string message instructing to use `CodebaseFolderSummaryTool` if top or second level codebase folders are found in searchable paths.



