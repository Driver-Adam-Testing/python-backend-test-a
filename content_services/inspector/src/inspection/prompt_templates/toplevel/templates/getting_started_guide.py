from utils.templates import S


PURPOSE_PROMPT = """
In a single paragraph of 3 to 5 sentences, provide a clear, concise statement of the codebase's purpose.
"""

PROBLEM_STATEMENT_PROMPT = """
Describe the problem(s) this codebase solves.
"""

FUNCTIONALITY_OVERVIEW_PROMPT = """
Provide a high-level overview of the codebase's functionality.
"""

TARGET_USER_ARCHETYPES_PROMPT = """
Describe the intended users of this codebase.
"""

USE_CASES_AND_USER_INTERACTIONS_PROMPT = """
List and briefly describe the main use cases and how users interact with the codebase.
"""

USER_JOURNEYS_PROMPT = """
List user journeys for the intended users of this codebase as a bulleted list. For each item in the list, use the following format:

As a user, I want to <X> so that I can <Y>, filling in X and Y.
"""

USER_INTERACTION_METHODS_PROMPT = """
Describe how users or developers interact with the codebase.
"""

CODEBASE_ORGANIZATION_AND_STRUCTURE_PROMPT = """
Explain the overall organization and structure of the codebase.
"""

MAJOR_MODULES_PROMPT = """
List and briefly describe the major modules or services unique to this codebase. Note: Do not include components that are standard to all similar projects.
"""

COMPONENT_INTERACTIONS_PROMPT = """
Explain how the key components of this codebase interact with each other.
"""

SETUP_AND_INSTALLATION_PROMPT = """
"Provide step-by-step instructions for setting up and installing the codebase."
"""

CONTINUED_EXPLORATION_PROMPT = """
Provide an outline for continuing to learn about this codebase.
"""


GETTING_STARTED_GUIDE_TEMPLATE = [
    (S.RAW,           "# Codebase Introduction",),
    (S.SINGLE_PROMPT, "## Purpose", PURPOSE_PROMPT),
    (S.SINGLE_PROMPT, "## Problem Statement", PROBLEM_STATEMENT_PROMPT),
    (S.SINGLE_PROMPT, "## Functionality Overview", FUNCTIONALITY_OVERVIEW_PROMPT),
    (S.RAW,           "# User Information",),
    (S.SINGLE_PROMPT, "## Target User Archetype(s)", TARGET_USER_ARCHETYPES_PROMPT),
    (S.SINGLE_PROMPT, "## Use Cases and User Interactions", USE_CASES_AND_USER_INTERACTIONS_PROMPT),
    (S.SINGLE_PROMPT, "## User Journeys", USER_JOURNEYS_PROMPT),
    (S.SINGLE_PROMPT, "## Interaction Methods", USER_INTERACTION_METHODS_PROMPT),
    (S.RAW,           "# Technical Overview",),
    (S.SINGLE_PROMPT, "## Codebase Organization and Structure", CODEBASE_ORGANIZATION_AND_STRUCTURE_PROMPT),
    # (S.SINGLE_PROMPT, "## Unique Aspects or Design Patterns", "Highlight any unique aspects or design patterns used in this codebase. Infer an answer to this by evaluating what you know about this codebase."),
    # (S.SINGLE_PROMPT, "## Codebase Type", "Specify the type of codebase, e.g., executable, library, SDK, API, frontend apps, backend service, data pipeline. Infer an answer to this by evaluating what you know about this codebase."),
    (S.SINGLE_PROMPT, "## Major Modules/Services", MAJOR_MODULES_PROMPT),
    (S.SINGLE_PROMPT, "## Component Interactions", COMPONENT_INTERACTIONS_PROMPT),
    (S.RAW,           "# Getting Started",),
    (S.SINGLE_PROMPT, "## Setup and Installation", SETUP_AND_INSTALLATION_PROMPT),
    # (S.SINGLE_PROMPT, "## Basic Usage Examples", "Offer simple examples demonstrating basic usage of the codebase"),
    (S.SINGLE_PROMPT, "## Continued Exploration", CONTINUED_EXPLORATION_PROMPT),
]
