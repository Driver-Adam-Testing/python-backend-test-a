# from document_generation_api.utils.dag import Dag, Node
import logging

import tiktoken
from shared.utils import decorators

logger = logging.getLogger(__name__)


def chunk_str(
    chunk_size: int,
    chunk_overlap: int,
    str_in: str,
) -> list[str]:
    num_chunks = len(str_in) // (chunk_size - chunk_overlap) + 1
    chunk_tick = chunk_size - chunk_overlap
    # Take advantage that slicing out of bounds doesn't cause an error
    return [
        str_in[(idx * chunk_tick) : ((idx + 1) * chunk_tick)]
        for idx in range(num_chunks)
    ]


@decorators.suppress_logging
def num_tokens_from_messages_open_ai(messages, model="gpt-3.5-turbo-0613"):
    """Return the number of tokens used by a list of messages when using open AI's chat completions API.

    Note, this code is taken from the openai cookbook, but modified for plain string messages. This is a
    rough estimate and should not be taken to be exact!

    https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        logger.warning("model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
        "gpt-4o-2024-08-06",
        "gpt-4o",
        "gpt-4o-mini",
    }:
        tokens_per_message = 3
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = (
            4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        )
    elif "gpt-3.5-turbo" in model:
        logger.warning(
            "gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613."
        )
        return num_tokens_from_messages_open_ai(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4" in model:
        logger.warning(
            "gpt-4 may update over time. Returning num tokens assuming gpt-4-0613."
        )
        return num_tokens_from_messages_open_ai(messages, model="gpt-4-0613")
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}.
            See https://github.com/openai/openai-python/blob/main/chatml.md for
            information on how messages are converted to tokens."""
        )
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        num_tokens += len(encoding.encode(message))
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens
