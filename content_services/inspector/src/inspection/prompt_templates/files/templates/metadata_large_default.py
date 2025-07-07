from shared.prompts.structured_prompting import (
    GENERAL_STE_STYLE_INSTRUCTION,
    NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_METADATA_PURPOSE,
    USE_BACKTICKS_STYLE_INSTRUCTION,
    Component,
    Prompt,
)
from utils.lang_specialization.metadata import (
    CONTENT_SUMMARY_PROMPT,
    METADATA_MEDIUM_AND_LARGE_SYSTEM_PROMPT,
    PURPOSE_PROMPT_LARGE,
)
from utils.templates import S

METADATA_LARGE_TEMPLATE = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        Prompt.empty()
        .append(Component(string=METADATA_MEDIUM_AND_LARGE_SYSTEM_PROMPT))
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .append(USE_BACKTICKS_STYLE_INSTRUCTION)
        .into_str(),
        Prompt.empty()
        .append(Component(string=PURPOSE_PROMPT_LARGE))
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_METADATA_PURPOSE)
        .into_str(),
    ),
    (
        S.SINGLE_PROMPT_TEXT,
        "# Content Summary",
        Prompt.empty()
        .append(Component(string=METADATA_MEDIUM_AND_LARGE_SYSTEM_PROMPT))
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str(),
        CONTENT_SUMMARY_PROMPT,
    ),
]
