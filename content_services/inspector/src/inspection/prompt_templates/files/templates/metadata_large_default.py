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
        METADATA_MEDIUM_AND_LARGE_SYSTEM_PROMPT,
        PURPOSE_PROMPT_LARGE,
    ),
    (
        S.SINGLE_PROMPT_TEXT,
        "# Content Summary",
        METADATA_MEDIUM_AND_LARGE_SYSTEM_PROMPT,
        CONTENT_SUMMARY_PROMPT,
    ),
]
