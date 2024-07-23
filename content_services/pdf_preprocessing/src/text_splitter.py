from typing import List


TOKEN = "token"


class TextChunk:
    def __init__(
        self, text: str, start_line: int, start_token: int, tokens: List[int]
    ) -> None:
        self.text = text
        self.start_line = start_line
        self.start_token = start_token
        self.tokens = tokens


class TextSplitter:
    """
    A class used to split text into chunks based on a specified model and token.
    """

    def __init__(
        self,
        model: str = "gpt-4",
        split_on: str = TOKEN,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ) -> None:
        """
        Parameters
        ----------
        model : str
            The model used for splitting (default is "gpt-4")
        split_on : str
            The token used for splitting (default is "token")
        chunk_size : int
            The size of each chunk (default is 512)
        chunk_overlap : int
            The overlap between chunks (default is 64)
        """

        self.model = model
        self.split_on = split_on
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> List[TextChunk]:
        """
        Splits the input text into chunks based on the specified model and token.

        Parameters
        ----------
        text : str
            The input text to be split.

        Returns
        -------
        list
            A list of TextChunk objects, each containing the chunk text, starting line number and starting overall token number.
        """
        chunks = []
        if self.split_on == TOKEN:
            import tiktoken

            encoder = tiktoken.encoding_for_model(self.model)
            tokens = list(encoder.encode(text))
            line_number = 0
            token_number = 0
            for i in range(0, len(tokens), self.chunk_size - self.chunk_overlap):
                chunk = tokens[i : i + self.chunk_size]
                chunks.append(
                    TextChunk(
                        text=encoder.decode(chunk),
                        start_line=line_number,
                        start_token=token_number,
                        tokens=chunk,
                    )
                )
                line_number += encoder.decode(chunk).count("\n") - encoder.decode(
                    chunk[: self.chunk_overlap]
                ).count("\n")
                token_number += len(chunk) - self.chunk_overlap
            return chunks

        raise NotImplementedError(
            "Splitting method not implemented for the given 'split_on' parameter"
        )
