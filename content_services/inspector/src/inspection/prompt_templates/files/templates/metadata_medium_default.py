from utils.lang_specialization.metadata import (
    METADATA_MEDIUM_AND_LARGE_SYSTEM_PROMPT,
    PURPOSE_PROMPT_MEDIUM,
)
from utils.templates import S

METADATA_MEDIUM_TEMPLATE = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        METADATA_MEDIUM_AND_LARGE_SYSTEM_PROMPT,
        PURPOSE_PROMPT_MEDIUM,
    ),
]
