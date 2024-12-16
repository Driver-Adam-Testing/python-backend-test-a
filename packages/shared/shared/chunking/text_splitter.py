from dataclasses import dataclass

import tiktoken

TOKEN = "token"


@dataclass
class TextChunk:
    text: str
    start_line: int
    start_token: int
    tokens: list[int]


def split_text(
    text: str,
    model: str = "gpt-4",
    split_on: str = TOKEN,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> list[TextChunk]:
    """
    Splits the input text into chunks based on the specified model and token.
    """
    chunks = []
    if split_on == TOKEN:
        encoder = tiktoken.encoding_for_model(model)
        tokens = list(encoder.encode(text, disallowed_special=()))
        line_number = 0
        token_number = 0
        for i in range(0, len(tokens), chunk_size - chunk_overlap):
            chunk = tokens[i : i + chunk_size]
            chunks.append(
                TextChunk(
                    text=encoder.decode(chunk),
                    start_line=line_number,
                    start_token=token_number,
                    tokens=chunk,
                )
            )
            line_number += encoder.decode(chunk).count("\n") - encoder.decode(
                chunk[:chunk_overlap]
            ).count("\n")
            token_number += len(chunk) - chunk_overlap
        return chunks

    raise NotImplementedError(
        "Splitting method not implemented for the given 'split_on' parameter"
    )
