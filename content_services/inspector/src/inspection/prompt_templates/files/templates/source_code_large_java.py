from utils.lang_specialization.default import (
    default_imports_checker,
)
from utils.lang_specialization.java import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_JAVA,
    class_dict_from_llm_java,
    interface_dict_from_llm_java,
    java_class_checker,
    java_interface_checker,
)
from utils.templates import S

SOURCE_CODE_LARGE_TEMPLATE_JAVA = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_JAVA,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    ),
    (
        S.LLM_COND_JSON,
        "# Imports and Dependencies",
        default_imports_checker,
        lambda _llm, output, _code: output,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Interfaces",
        java_interface_checker,
        interface_dict_from_llm_java,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Classes",
        java_class_checker,
        class_dict_from_llm_java,
        None,
    ),
]
