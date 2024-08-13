import os

from openai import AsyncOpenAI, OpenAI
from shared.chunking.text_splitter import TextChunk

TEXT_EMBEDDING_MODEL = os.getenv("TEXT_EMBEDDING_MODEL", "text-embedding-3-small")
SUPPORTED_OPENAI_MODELS = ["text-embedding-3-small"]


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

    openai_client = OpenAI()
    prepared_chunks = _prepare_text_chunks(text_chunks)
    return [
        t.embedding
        for t in openai_client.embeddings.create(
            input=prepared_chunks, model=model
        ).data
    ]


async def async_batch_embed_text(
    text_chunks: list[str | TextChunk], model: str = TEXT_EMBEDDING_MODEL
) -> list:
    if model not in SUPPORTED_OPENAI_MODELS:
        raise ValueError(f"Model {model} is not supported.")

    openai_client = AsyncOpenAI()
    prepared_chunks = _prepare_text_chunks(text_chunks)
    response = await openai_client.embeddings.create(input=prepared_chunks, model=model)
    return [t.embedding for t in response.data]
