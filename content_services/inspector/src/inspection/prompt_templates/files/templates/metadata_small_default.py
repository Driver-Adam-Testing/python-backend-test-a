from utils.lang_specialization.metadata import (
    METADATA_SMALL_SYSTEM_PROMPT,
    PURPOSE_PROMPT_SMALL,
)
from utils.templates import S

METADATA_SMALL_TEMPLATE = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        METADATA_SMALL_SYSTEM_PROMPT,
        PURPOSE_PROMPT_SMALL,
    ),
]
