# Purpose
This Python code defines a template for a "Getting Started Guide" for a codebase, utilizing a structured format to ensure comprehensive documentation. It imports a utility module for handling templates and defines a series of prompts that guide the documentation process, covering aspects such as the codebase's purpose, problem statement, functionality, user interactions, and technical overview. The code is essentially a configuration file that outlines the sections and prompts needed to create a detailed and organized guide, making it easier for users and developers to understand and interact with the codebase. The functionality is narrow, focusing specifically on documentation generation, and it is intended for use by developers or technical writers who need to document software projects.
# Imports and Dependencies

---
- `utils.templates`


# Global Variables

---
### CODEBASE_ORGANIZATION_AND_STRUCTURE_PROMPT 
- **Type**: `str`
- **Description**: `CODEBASE_ORGANIZATION_AND_STRUCTURE_PROMPT` is a string variable that contains a prompt asking for an explanation of the overall organization and structure of a codebase. This prompt is likely used in a documentation or template generation context to guide users in providing detailed information about how a codebase is organized.
- **Use**: This variable is used to prompt users to describe the organization and structure of a codebase, likely as part of a documentation or template generation process.


---
### COMPONENT_INTERACTIONS_PROMPT 
- **Type**: `str`
- **Description**: `COMPONENT_INTERACTIONS_PROMPT` is a string variable that contains a prompt asking for an explanation of how the key components of a codebase interact with each other. This prompt is likely used in documentation or templates to guide users or developers in providing detailed information about component interactions.
- **Use**: This variable is used as a template prompt to elicit detailed descriptions of component interactions within a codebase.


---
### CONTINUED_EXPLORATION_PROMPT 
- **Type**: `str`
- **Description**: The `CONTINUED_EXPLORATION_PROMPT` is a string variable that contains a prompt asking for an outline to continue learning about the codebase. It is part of a series of prompts designed to guide the documentation and understanding of a software project.
- **Use**: This variable is used to provide a template prompt for users or developers to outline further exploration and learning about the codebase.


---
### FUNCTIONALITY_OVERVIEW_PROMPT 
- **Type**: `str`
- **Description**: `FUNCTIONALITY_OVERVIEW_PROMPT` is a string variable that contains a prompt asking for a high-level overview of the codebase's functionality. It is used as part of a template for generating documentation or guides related to the codebase.
- **Use**: This variable is used to prompt users or developers to provide a summary of the codebase's functionality, which is then included in documentation or guides.


---
### GETTING_STARTED_GUIDE_TEMPLATE 
- **Type**: `list`
- **Description**: `GETTING_STARTED_GUIDE_TEMPLATE` is a list that defines the structure and content of a getting started guide for a codebase. It consists of tuples, each containing a type of content (e.g., `S.RAW` or `S.SINGLE_PROMPT_TEXT`), a section title, and an optional prompt variable that provides detailed instructions or questions to be addressed in that section. This template is designed to guide users through understanding the codebase's purpose, user interactions, technical details, and setup instructions.
- **Use**: This variable is used to generate a comprehensive and structured getting started guide for users of the codebase.


---
### MAJOR_MODULES_PROMPT 
- **Type**: `str`
- **Description**: `MAJOR_MODULES_PROMPT` is a string variable that contains a prompt asking for a list and brief description of the major modules or services unique to a specific codebase. It is part of a series of prompts designed to gather comprehensive documentation about a codebase.
- **Use**: This variable is used to prompt users to provide information about the unique major modules or services in a codebase, excluding standard components.


---
### PROBLEM_STATEMENT_PROMPT 
- **Type**: `str`
- **Description**: The `PROBLEM_STATEMENT_PROMPT` is a string variable that contains a prompt asking for a description of the problem(s) that the codebase solves. It is part of a series of prompts used to gather detailed documentation about a codebase.
- **Use**: This variable is used to prompt users or developers to provide a description of the problems addressed by the codebase, which is likely part of a larger documentation or onboarding process.


---
### PURPOSE_PROMPT 
- **Type**: `str`
- **Description**: The `PURPOSE_PROMPT` variable is a string that contains a template prompt asking for a concise statement of the codebase's purpose. It is designed to elicit a paragraph of 3 to 5 sentences that clearly articulates the overall goal and intent of the codebase.
- **Use**: This variable is used as a prompt template to guide users or developers in providing a clear and concise description of the codebase's purpose.


---
### SETUP_AND_INSTALLATION_PROMPT 
- **Type**: `str`
- **Description**: The `SETUP_AND_INSTALLATION_PROMPT` is a string variable that contains a prompt asking for step-by-step instructions for setting up and installing the codebase. It is part of a series of prompts used to guide the creation of documentation for a codebase.
- **Use**: This variable is used to prompt users or developers to provide detailed setup and installation instructions for the codebase.


---
### TARGET_USER_ARCHETYPES_PROMPT 
- **Type**: `str`
- **Description**: `TARGET_USER_ARCHETYPES_PROMPT` is a string variable that contains a prompt asking for a description of the intended users of the codebase. It is part of a series of prompts used to gather detailed documentation about the codebase.
- **Use**: This variable is used to prompt users or developers to describe the target user archetypes for the codebase, aiding in the creation of comprehensive documentation.


---
### USER_INTERACTION_METHODS_PROMPT 
- **Type**: `str`
- **Description**: `USER_INTERACTION_METHODS_PROMPT` is a string variable that contains a prompt asking for a description of how users or developers interact with the codebase. It is part of a series of prompts designed to gather comprehensive documentation about a codebase.
- **Use**: This variable is used to prompt users to provide information on the interaction methods with the codebase, which is then likely used in documentation or guides.


---
### USER_JOURNEYS_PROMPT 
- **Type**: `str`
- **Description**: `USER_JOURNEYS_PROMPT` is a string variable that contains a template prompt for listing user journeys in a codebase. It instructs the user to list these journeys in a bulleted format, specifying the user's goals and motivations.
- **Use**: This variable is used to guide the documentation process by providing a structured format for describing user journeys in the codebase.


---
### USE_CASES_AND_USER_INTERACTIONS_PROMPT 
- **Type**: `str`
- **Description**: The `USE_CASES_AND_USER_INTERACTIONS_PROMPT` is a string variable that contains a prompt asking for a list and brief description of the main use cases and user interactions with the codebase. It is part of a series of prompts designed to gather comprehensive documentation about a codebase.
- **Use**: This variable is used to guide users or developers in documenting the primary use cases and user interactions for the codebase.


