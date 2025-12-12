import os
from itertools import batched
from json.decoder import JSONDecodeError

from openai import (
    APIConnectionError,
    APITimeoutError,
    AsyncOpenAI,
    BadRequestError,
    InternalServerError,
    OpenAI,
    PermissionDeniedError,
    RateLimitError,
)
from shared.chunking.text_splitter import TextChunk
from shared.utils.decorators import async_retry_with_exponential_backoff

TEXT_EMBEDDING_MODEL = os.getenv("TEXT_EMBEDDING_MODEL", "text-embedding-3-small")
SUPPORTED_OPENAI_MODELS = ["text-embedding-3-small"]
BATCH_SIZE = 500  # OpenAI's max batch is 300k tokens, we max at 512 tokens * 500 batches = 256k tokens


def _prepare_text_chunks(text_chunks: list[str | TextChunk]) -> list[str]:
    if all(isinstance(chunk, TextChunk) for chunk in text_chunks):
        return [chunk.text for chunk in text_chunks]
    elif not all(isinstance(chunk, str) for chunk in text_chunks):
        raise TypeError("text_chunks must be a list of strings or a list of TextChunks")
    return text_chunks


def batch_embed_text(
    text_chunks: list[str | TextChunk], model: str = TEXT_EMBEDDING_MODEL
) -> list:
    if model not in SUPPORTED_OPENAI_MODELS:
        raise ValueError(f"Model {model} is not supported.")

    if os.environ.get("AZURE_OPENAI_BASE_URL"):
        base_url = os.environ["AZURE_OPENAI_BASE_URL"]
        base_url = f"https://{base_url}/openai/v1/"
        api_key = os.environ["AZURE_OPENAI_KEY_1"]
        openai_client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
    else:
        openai_client = OpenAI()
    prepared_chunks = _prepare_text_chunks(text_chunks)
    return [
        t.embedding
        for t in openai_client.embeddings.create(
            input=prepared_chunks, model=model
        ).data
    ]


@async_retry_with_exponential_backoff(
    initial_delay=10.0,
    exponential_base=1.0005,
    errors=(
        APITimeoutError,
        RateLimitError,
        APIConnectionError,
        InternalServerError,
        JSONDecodeError,
        PermissionDeniedError,
    ),
)
async def async_batch_embed_text(
    text_chunks: list[str | TextChunk], model: str = TEXT_EMBEDDING_MODEL
) -> list:
    if model not in SUPPORTED_OPENAI_MODELS:
        raise ValueError(f"Model {model} is not supported.")

    if os.environ.get("AZURE_OPENAI_BASE_URL"):
        base_url = os.environ["AZURE_OPENAI_BASE_URL"]
        base_url = f"https://{base_url}/openai/v1/"
        api_key = os.environ["AZURE_OPENAI_KEY_1"]
        openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    else:
        openai_client = AsyncOpenAI()
    prepared_chunks = _prepare_text_chunks(text_chunks)
    embeddings = []
    try:
        for batch in batched(prepared_chunks, BATCH_SIZE):
            response = await openai_client.embeddings.create(input=batch, model=model)
            embeddings.extend([t.embedding for t in response.data])
    except BadRequestError:
        # There appears to be a mismatch in the number of tokens in the batch
        # when splitting up text with tiktoken and what the openAI api sees.
        # This is a bandaid fix to prevent the error, but should better root cause.
        for batch in batched(prepared_chunks, int(BATCH_SIZE / 4)):
            response = await openai_client.embeddings.create(input=batch, model=model)
            embeddings.extend([t.embedding for t in response.data])

    return embeddings
