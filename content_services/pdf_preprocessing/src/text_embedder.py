import os
from typing import List, Union

from openai import OpenAI

TEXT_EMBEDDING_MODEL = os.getenv("TEXT_EMBEDDING_MODEL", "text-embedding-3-small")
SUPPORTED_OPENAI_MODELS = ["text-embedding-3-small"]
from .text_splitter import TextChunk


class TextEmbedder:
    """
    A class used to embed text using a specified model.

    Attributes
    ----------
    model : str
        The model used for text embedding.

    Methods
    -------
    batch_embed_text(text_chunks: Union[List[str], List[TextChunk]]) -> List:
        Embeds a batch of text chunks using the specified model.
    """

    def __init__(self, model: str = TEXT_EMBEDDING_MODEL) -> None:
        """
        Parameters
        ----------
        model : str, optional
            The model used for text embedding (default is TEXT_EMBEDDING_MODEL)
        """
        self.model = model

    def batch_embed_text(self, text_chunks: Union[List[str], List[TextChunk]]) -> List:
        """
        Embeds a batch of text chunks using the specified model.

        Parameters
        ----------
        text_chunks : Union[List[str], List[TextChunk]]
            A list of text chunks to be embedded. The chunks can be either strings or TextChunk objects.

        Returns
        -------
        list
            A list of embeddings for the input text chunks.

        Raises
        ------
        TypeError
            If the input text chunks are not a list of strings or a list of TextChunk objects.
        ValueError
            If the specified model is not supported.
        """
        if self.model in SUPPORTED_OPENAI_MODELS:
            openai_client = OpenAI()
            if all(isinstance(chunk, TextChunk) for chunk in text_chunks):
                text_chunks = [chunk.text for chunk in text_chunks]
            elif not all(isinstance(chunk, str) for chunk in text_chunks):
                raise TypeError(
                    "text_chunks must be a list of strings or a list of TextChunks"
                )
            return [
                t.embedding
                for t in openai_client.embeddings.create(
                    input=text_chunks, model=self.model
                ).data
            ]
        else:
            raise ValueError(f"Model {self.model} is not supported.")
