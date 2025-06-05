from utils.lang_specialization.ir_common import ListData
from utils.lang_specialization.java import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_JAVA,
    JavaClassCollection,
    JavaClassRawSymbolCollection,
    JavaImportRawSymbolCollection,
    JavaInterfaceCollection,
    JavaInterfaceRawSymbolCollection,
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
        S.FN_COND_JSON,
        "# Imports and Dependencies",
        JavaImportRawSymbolCollection.from_static_analysis,
        lambda _llm, output, _code: ListData(data=list(output.data.keys())),
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Interfaces",
        JavaInterfaceRawSymbolCollection.from_static_analysis,
        JavaInterfaceCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Classes",
        JavaClassRawSymbolCollection.from_static_analysis,
        JavaClassCollection.from_llm,
        None,
    ),
]
