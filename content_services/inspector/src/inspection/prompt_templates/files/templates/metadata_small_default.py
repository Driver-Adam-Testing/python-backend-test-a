from utils.lang_specialization.metadata import (
    METADATA_SMALL_SYSTEM_PROMPT,
    PURPOSE_PROMPT_SMALL,
)
from utils.prompts import (
    GENERAL_STE_STYLE_INSTRUCTION,
    NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_METADATA_PURPOSE,
    Component,
    Prompt,
)
from utils.templates import S

METADATA_SMALL_TEMPLATE = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        Prompt.empty()
        .append(Component(string=METADATA_SMALL_SYSTEM_PROMPT))
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str(),
        Prompt.empty()
        .append(Component(string=PURPOSE_PROMPT_SMALL))
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_METADATA_PURPOSE)
        .into_str(),
    ),
]
