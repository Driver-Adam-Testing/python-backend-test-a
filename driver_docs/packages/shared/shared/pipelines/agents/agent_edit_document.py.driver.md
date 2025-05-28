# Purpose
This Python code file is designed to facilitate a smart instruction generation process for editing documents. It is structured as a library module that defines data models and a function to execute a document editing pipeline. The primary components include the `EditDocumentContext` and `AgentEditDocumentExecuteInput` classes, which are Pydantic models used to encapsulate the context and input data for the editing process. The `EditDocumentContext` class captures the text surrounding a selected portion of a document, while the `AgentEditDocumentExecuteInput` class includes the initial prompt and context necessary for generating instructions.

The core functionality is provided by the `run_agent_edit_document` function, which orchestrates a multi-step pipeline to process and edit the selected text. This function leverages several imported tools and agents, such as `run_agent_prompt_augmentation`, `run_agent_default`, and `run_agent_copy_editor`, to enhance the prompt, generate default agent results, and perform copy editing, respectively. The function configures these agents with specific parameters, such as the number of iterations and tool names, to ensure a comprehensive editing process. The final output is encapsulated in a `PipelineStepResponse`, which includes the edited text and any search results generated during the process. This code is intended to be part of a larger system where it can be imported and utilized to automate document editing tasks based on user prompts.
# Imports and Dependencies

---
- `pydantic.BaseModel`
- `shared.agent.tools.open_file_tool.OpenFileTool`
- `shared.agent.tools.search_tool.SearchTool`
- `shared.interfaces.agents.data_scope.DataScope`
- `shared.interfaces.agents.pipeline_configuration.AgentConfiguration`
- `shared.interfaces.agents.pipeline_configuration.PipelineInput`
- `shared.interfaces.agents.pipeline_configuration.PipelineStepResponse`
- `shared.interfaces.agents.pipeline_configuration.PipelineStepType`
- `shared.pipelines.agents.agent_copy_editor.run_agent_copy_editor`
- `shared.pipelines.agents.agent_default.run_agent_default`
- `shared.pipelines.agents.agent_prompt_augmentation.run_agent_prompt_augmentation`


# Global Variables

---
### INSTRUCTION_PROMPT 
- **Type**: `str`
- **Description**: The `INSTRUCTION_PROMPT` is a string variable that contains a predefined instruction for rewriting a selected part of a document. It specifies that the response should be a replacement or appended text for the selected text, formatted as markdown, based on the user's prompt.
- **Use**: This variable is used as part of the system prompts in the `run_agent_edit_document` function to guide the text editing process.


# Classes

---
### AgentEditDocumentExecuteInput 
- **Type**: `class`
- **Members**:
    - `prompt`: The initial prompt for generating instructions.
    - `context`: The context surrounding the selected text.
    - `scope`: The data scope within which the instructions are generated.
- **Description**: The `AgentEditDocumentExecuteInput` class is a specialized input model designed for smart instruction generation within a document editing pipeline. It inherits from `PipelineInput` and includes attributes such as `prompt`, which serves as the initial instruction prompt, `context`, which provides the surrounding text context using the `EditDocumentContext` class, and `scope`, which defines the data scope for the operation. This class is integral to the process of generating and executing document editing instructions in a structured and context-aware manner.
- **Inherits From**:
    - PipelineInput


---
### EditDocumentContext 
- **Type**: `class`
- **Members**:
    - `text_before_selection`: The text before the selected portion.
    - `selected_text`: The text that has been selected.
    - `text_after_selection`: The text after the selected portion.
- **Description**: The `EditDocumentContext` class is a data model that provides a structured context for smart instruction generation, specifically focusing on text editing tasks. It inherits from `BaseModel` and includes three string attributes: `text_before_selection`, `selected_text`, and `text_after_selection`, which represent the text surrounding a selected portion in a document. This context is crucial for generating instructions or modifications related to the selected text.
- **Inherits From**:
    - BaseModel


# Functions

---
### run_agent_edit_document 
The `run_agent_edit_document` function orchestrates a multi-step process to edit a document based on a given prompt and context, utilizing various agent configurations and tools.
- **Inputs**:
    - `input`: An instance of `AgentEditDocumentExecuteInput` containing the initial prompt, context, and scope for the document editing process.
- **Control Flow**:
    - Initialize a `AgentConfiguration` object using the input's agent configuration and set its iterations to 1.
    - Call `run_agent_prompt_augmentation` with a `PipelineInput` constructed from the input's prompt, context, and the modified agent configuration to generate an augmented prompt.
    - Execute `run_agent_default` with the augmented prompt's result and a new `AgentConfiguration` that includes specific system prompts, iterations set to 3, and tool names `SearchTool` and `OpenFileTool`.
    - Run `run_agent_copy_editor` with the result from the default agent and a `AgentConfiguration` for the copy editor with iterations set to 1.
    - Return a `PipelineStepResponse` containing the final agent result, search results from the default agent, and the agent ID.
- **Output**:
    - A `PipelineStepResponse` object containing the final agent result, search results, and agent ID from the document editing process.


