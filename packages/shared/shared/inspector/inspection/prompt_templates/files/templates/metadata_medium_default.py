from shared.inspector.utils.lang_specialization.metadata import (
    METADATA_MEDIUM_AND_LARGE_SYSTEM_PROMPT,
    PURPOSE_PROMPT_MEDIUM,
)
from shared.inspector.utils.templates import S
from shared.prompts.structured_prompting import (
    GENERAL_STE_STYLE_INSTRUCTION,
    NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_METADATA_PURPOSE,
    USE_BACKTICKS_STYLE_INSTRUCTION,
    Component,
    Prompt,
)

METADATA_MEDIUM_TEMPLATE = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        Prompt.empty()
        .append(Component(string=METADATA_MEDIUM_AND_LARGE_SYSTEM_PROMPT))
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .append(USE_BACKTICKS_STYLE_INSTRUCTION)
        .into_str(),
        Prompt.empty()
        .append(Component(string=PURPOSE_PROMPT_MEDIUM))
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_METADATA_PURPOSE)
        .into_str(),
    ),
]
