# MCP Tools for This Project

## Available Tools

Driver is a toolset that provides pre-computed and dense information about codebases, exposed through MCP. You should use these tools to aid in your navigation, discovery, and reasoning about codebases you are working with. This can ensure you are able to accomplish your tasks much more quickly and more exhaustively, reducing the risk you will miss important context about the codebase. Prioritize use of Driver's MCP tools in this manner.

Almost all of these tools require you to provide the name of the codebase as input. You will need to understand the context you are running in (e.g., what local codebase you are being asked to work with) and match that with the codebase supported by Driver.

- Use the `get_codebase_names` tool to get a list of codebases supported by Driver.
- If needed, use local tools such as `git` or OS-level directory tools like the `pwd` (Unix-like contexts) to look for the name of the codebase you are working with locally.
- Match your understanding of the local codebase context against the valid list returned from `get_codebase_names` to make sure you can use the Driver MCP tools properly.

There are two major categories of tools in the Driver MCP service:

1. Deep Context Documents: static documents that provide dense and complete compilations, such as architecture, onboarding guides, and change logs.
2. Granular Navigational Tools: More granular and structured tools to aid in navigation, discovery, and surface lower-level documentation.

## Deep Context Tools
These are static documents (typically 1 -- 2 pages in length) that provide dense and complete compilations of critical information. Use and read these documents early in your workflows to immediately get critical context and best plan your next steps given holistic and exhauxtive context. At the beginning of a session, always read each of the deep context documents to get oriented with the codebase well for all future tasks.

### get_architecture_guide
- **Purpose**: Returns a one page document describing, exhuastively and densely, the architecture of the whole codebase, optimized to inform an LLM agent.
- **When to Use**: At the beginning of a workflow triggered by user input, **especially** if the user's query/input/task requires broad or holistic architecture knowledge.

### get_llm_onboarding_guide
- **Purpose**: Returns a one page document intended to best onboard an LLM agent/host/client quickly to the codebase, providing a broad understanding of the codebase, where to look for certain topics and why, and providing navigation and cross-referencing tips.
- **When to Use**: At the beginning of a session or any query from the user, **especially** if the user's query requires a broader understanding of the codebase and navigating it.

### get_changelog
- **Purpose**: Returns a document with an exhaustive change log, broken down by year and month, describing the development process for this codebase over time. This can provide rich information about intent and "the why" for components of the codebase that are not possible to understand looking at any single state/snapshot of the codebase.
- **When to Use**: At the beginning of a workflow triggered by user input in which information about the historical development of the codebase could be useful. Examples include if the user is asking you to think about how a new feature should be implemented or extended or refactored. By consulting the change log and historical development first, you will be better positioned to reason about these kind of decisions.

## Grangular Navigation Tools

### get_code_map
- **Purpose**: A navigable tree structure for the codebase queryable at any place in the directory structure that will return terse descriptions and metadata for that node and children up to a specified depth.
- **When to Use**: Anywhere in your workflow where detailed understanding about various parts of the codebase is useful. Use this to understand important files/folders and then you can call other tools to read documentation for these files/folders or directly read the source material.

### get_file_documentation
- **Purpose**: Fetch complete and exhaustive symbol-level documentation for the file specified by path.
- **When to Use**: When you need to understand a file at the detailed symbol-level. Very useful in tandem with `get_code_map`, which gives you precise path and purpose information for files and `get_file_documentation` can be used to drill down into the details of the most important files.

### get_detailed_changelog
- **Purpose**: Fetch detailed change log and commit log-derived information for a particular month and year. This can provide detailed and rich information about intent and the development process.
- **When to Use**: When detailed historical development information from a particular point in time is helpful. For example, you are working with a user to update, refactor, or modify a major feature in a codebase and knowing the development history may help. You will likely always want to call `get_changelog` first to get your bearings overall on the development history, then use `get_detailed_changelog` to zoom in on the details from a particular time period (e.g., when a relevant part of the codebase was under major development).

## Other Utility Tools

### get_codebase_entry_points
- **Purpose**: Returns a list of primary entry points for the codebase, with the path and a short description.
- **When to Use**: When orienting yourself with a codebase and a list of a few of the critical entry points (such as `main` executable locations, library entry points, or scripts) would be usueful.

## Suggested Workflows Using Multiple Tools in Concert

1. Read Deep Context Docs when you start a session and up front when performing tasks as needed. This can quickly and significantly improve your subsequent planning and execution to solve user tasks.
2. When detailed discovery is required, use `get_code_map` and `get_file_documentation` in tandem to effectively navigate, find, and read detailed information.
3. When the "intent" and "why" of a codebase and its historical development is valuable, use `get_changelog` and `get_detailed_changelog` in tandem as needed tp explore historical development content.
