from shared.prompts.structured_prompting import (
    GENERAL_STE_STYLE_INSTRUCTION,
    NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_CODE_PURPOSE,
    USE_BACKTICKS_STYLE_INSTRUCTION,
    Component,
    Prompt,
)
from utils.lang_specialization.verilog import (
    SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
    SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_VERILOG,
    VerilogFnTaskCollection,
    VerilogFnTaskRawSymbolCollection,
    VerilogModuleCollection,
    VerilogModuleRawSymbolCollection,
)
from utils.templates import S

SOURCE_CODE_SMALL_TEMPLATE_VERILOG = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        Prompt.empty()
        .append(Component(string=SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_VERILOG))
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .append(USE_BACKTICKS_STYLE_INSTRUCTION)
        .into_str(),
        Prompt.empty()
        .append(Component(string=SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT))
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_CODE_PURPOSE)
        .into_str(),
    ),
    (
        S.FN_COND_JSON,
        "# Modules",
        VerilogModuleRawSymbolCollection.from_static_analysis,
        VerilogModuleCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions and Tasks",
        VerilogFnTaskRawSymbolCollection.from_static_analysis,
        VerilogFnTaskCollection.from_llm,
        None,
    ),
]
