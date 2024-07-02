import textwrap
from pathlib import Path

from utils.llm import num_tokens_from_messages_open_ai
from utils.io import get_prompt_template
from utils.dag import LiteNode
import copy

from utils.models import ChatOpenAI

from utils.codemap_ctags import extract_symbols_w_ctags

PARENT_PATH = Path(__file__).parent


def extract_context_lines(
    file_content: str,
    target_line_start: int,
    target_line_end: int,
    padding_lines_top: int = 100,
    padding_lines_bottom: int = 100,
) -> str:
    lines = file_content.splitlines()
    actual_start = max(
        0, target_line_start - 1 - padding_lines_top
    )  # -1 because line indices are 1-based
    actual_end = min(len(lines), target_line_end + padding_lines_bottom)

    context_lines = lines[actual_start:actual_end]
    return "\n".join(context_lines)


def _document_symbol(
    symbol: dict[str, any], file_node, file_description_paragraph, file_content
) -> dict[str, any]:
    try:
        # print(f"Documenting symbol `{symbol['name']}` in `{file_node.root_rel_path}`")
        context = extract_context_lines(
            file_content=file_content,
            target_line_start=symbol["line"],
            target_line_end=symbol.get("end", symbol["line"]),
        )
        # Create a copy of the symbol to work on. We're being defensive and making a deep copy.
        updated_symbol = copy.deepcopy(symbol)
        updated_symbol["context"] = context

        try:
            (
                symbol_description,
                model_used,
            ) = symbol_single_paragraph_from_code_and_file_description(
                file_name=file_node.root_rel_path,
                file_description=file_description_paragraph,  # file_doc["short"]["single_paragraph"],
                symbol_name=symbol["name"],
                symbol_kind=symbol["kind"],
                code_context=context,
            )
        except ContextSizeError:
            print(
                f"Context size exceeded for symbol `{symbol['name']}`. Not documenting, but "
                f"context was captured for debugging purposes."
            )
            updated_symbol["description"] = None
        else:
            updated_symbol["description"] = symbol_description
            updated_symbol["model_used"] = model_used
        return updated_symbol
    except Exception as exc:
        print(
            f"Error documenting symbol `{symbol['name']}`: {exc}\nContinuing without adding symbol description..."
        )
        # Return the original symbol unmodified to ensure no partial updates are applied on error
        return symbol


def document_symbols_in_file(
    file_node: LiteNode,
    source_code: str,
    file_description_paragraph: str,
    symbol_count_limit: int | None = None,
) -> list[dict[str, any]]:

    # TODO revert; temporarily silence printing
    import sys, io
    sys.stdout = io.StringIO()



    print(f"Extracting and documenting symbols in `{file_node.root_rel_path}`")
    file_content = source_code
    if len(file_content.strip()) == 0:
        print(
            f"Empty file `{file_node.root_rel_path}` found when attempting to document symbols."
        )
        return []

    try:
        symbols = extract_symbols_w_ctags(root_rel_path=file_node.root_rel_path, file_content=source_code)
    except Exception as e:
        print(f"Failed to extract symbols from `{file_node.root_rel_path}`: {e}")
        return []

    print(f"Extracted {len(symbols)} symbols from `{file_node.root_rel_path}`")

    if len(symbols) == 0:
        print(f"No symbols found in file `{file_node.root_rel_path}`.")
        return []

    if symbol_count_limit is not None and len(symbols) > symbol_count_limit:
        print(
            f"Too many symbols found in file `{file_node.root_rel_path}`: {len(symbols)}. "
            f"Limit: {symbol_count_limit}. Omitting symbols for this file from output..."
        )
        return []

    symbols.sort(key=lambda x: x["line"])

    # TODO parallelize this further with modal or threads. See old code for reference to add back async
    # Modal function approach is probably better if we are to swap in our own models
    results = [
        _document_symbol(symbol, file_node, file_description_paragraph, file_content)
        for symbol in symbols
    ]

    # Ensure symbols are replaced with their updated versions from results
    symbols = results

    # Pop this off since it's big and only used for debugging
    for symbol in symbols:
        if "context" in symbol:
            symbol.pop("context")

    # Remove model_used keys from the symbols; we persisted that to disk for debugging only
    for symbol in symbols:
        if "model_used" in symbol:
            symbol.pop("model_used")

    return symbols


class ContextSizeError(Exception):
    def __init__(self, message="Context size exceeds the maximum limit"):
        self.message = message
        super().__init__(self.message)


def symbol_single_paragraph_from_code_and_file_description(
    file_name: str,
    file_description: str,
    symbol_name: str,
    symbol_kind: str,
    code_context: str,
) -> tuple[str, str]:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/files/single_paragraph_symbol_description.txt"
    )
    human_prompt = textwrap.dedent(
        f"""
        source file: {file_name}

        file description: {file_description}

        symbol name: {symbol_name}

        symbol kind: {symbol_kind}

        code context:
    """
    )
    human_prompt += f"```\n{code_context}\n```"

    # Select model based on input context size
    req_timeout = 300
    temperature = 0
    max_tokens_paragraph = (
        800  # Very conservative estimate for a paragraph's worth of tokens
    )
    model_limits = {
        "gpt-3.5-turbo": 16_385 - max_tokens_paragraph,
        "gpt-4-turbo": 128_000 - max_tokens_paragraph,
    }

    def select_model(input_tokens: int):
        for model_name, token_limit in model_limits.items():
            if input_tokens <= token_limit:
                return model_name
        raise ContextSizeError(
            f"Input context size {input_tokens} exceeds all available model limits"
        )

    # Assume token counts for 3.5 turbo and 4 turbo are the same (True today)
    input_tokens = num_tokens_from_messages_open_ai(
        [system_prompt, human_prompt], "gpt-3.5-turbo"
    )

    selected_model_name = select_model(input_tokens)
    print(f"Selected model for symbol `{symbol_name}`: {selected_model_name}")

    llm = ChatOpenAI(
        model=selected_model_name, temperature=temperature, request_timeout=req_timeout
    )

    description = llm.generate_response(system_prompt, human_prompt)
    return (description, selected_model_name)
