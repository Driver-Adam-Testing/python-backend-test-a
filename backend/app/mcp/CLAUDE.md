# MCP Tools for This Project

## Available Tools

Driver's tools all work by providing pre-computed and dense information about the codebase. You should use these tools to aid in your navigation, discovery, and reasoning about codebases you are working with. This can ensure you are able to accomplish your tasks much more quickly and more exhaustively, reducing the risk you will miss important context about the codebase. Prioritize use of Driver's tools in this manner.

Almost all of these tools require you to provide the name of the codebase as input. You will need to understand the context you are running in (e.g., what local codebase you are being asked to work with) and match that with the codebase supported by the Driver MCP.

- Use the `get_codebase_names` tool to get a list of codebases supported by Driver.
- If needed, use local tools such as `git` or OS-level directory tools like the `pwd` (Unix-like contexts) to look for the name of the codebase you are working with locally.
- Match your understanding of the local codebase context against the valid list returned from `get_codebase_names` to make sure you can use the Driver MCP tools properly.

There are two major categories of tools in the Driver MCP service:

1. Deep Context Documents: static documents that provide dense and complete compilations, such as architecture, onboarding guides, and 
2. Granular Navigational Tools

## Deep Context Tools
These are static documents (typically 1 -- 2 pages in length) that provide dense and complete compilations of critical information. Use and read these documents early in your workflows to immediately get critical context and best plan your next steps given holistic and exhauxtive context.

### get_architecture_guide
- **Purpose**: Returns a one page document describing, exhuastively and densely, the architecture of the whole codebase, optimized to inform an LLM agent.
- **When to Use**: At the beginning of a workflow triggered by user input, **especially** if the user's query/input/task requires broad or holistic architecture knowledge.

### get_llm_onboarding_guide
- **Purpose**: Returns a one page document intended to best onboard an LLM agent/host/client quickly to the codebase, providing a broad understanding of the codebase, where to look for certain topics and why, and providing navigation and cross-referencing tips.
- **When to Use**: At the beginning of a session or any query from the user, **especially** if the user's query requires a broader understanding of the codebase and navigating it.

### get_changelog
- **Purpose**: returns a document with an exhaustive change log, broken down by year and month, describing the development process for this codebase over time. This can provide rich information about intent and "the why" for components of the codebase that are not possible to understand looking at any single state/snapshot of the codebase.
- **When to Use**: At the beginning of a workflow triggered by user input in which information about the historical development of the codebase could be useful.

## Grangular Navigation Tools

### get_code_map
- **Purpose**: A navigable tree structure for the codebase queryable at any place in the directory structure that will return terse descriptions and metadata for that node and children up to a specified depth.
- **When to Use**: Anywhere in your workflow where detailed understanding about various parts of the codebase is useful. Use this to understand important files/folders and then you can call other tools to read documentation for these files/folders or directly read the source material.

### fetch_tech_doc
- **Purpose**: Fetch complete and exhaustive documentation for the file or folder specified by path. For files, this will include detailed symbol-level documentation.
- **When to Use**: When you want to understand a file at the detailed symbol-level but without looking at the raw source code.

## Other Utility Tools

### get_codebase_entry_points
- **Purpose**: Returns a list of primary entry points for the codebase, with the path and a short description.
- **When to Use**: When orienting yourself with a codebase and the critical entry points (such as `main` executable locations, library entry points, or scripts).

## Suggested Workflows Using Multiple Tools in Concert

1. Read Deep Context Docs up front when performing tasks.
2. When detailed discovery is required, use `get_code_map` and `fetch_tech_doc` in tandem to effectively navigate, find, and read detailed information.
