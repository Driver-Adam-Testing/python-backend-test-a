from numpy import dot
from numpy.linalg import norm
from shared.embedding.text_embedder import batch_embed_text


class SemanticComparator:
    def __init__(self):
        self.entries = []

    def add_entry(self, name: str, description: str):
        """
        Add a new entry with a name and description. The embedding is generated within this method.

        Args:
            name (str): The name of the entry.
            description (str): A brief description of the entry.
        """
        embedding = batch_embed_text([description])[0]
        self.entries.append(
            {"name": name, "description": description, "embedding": embedding}
        )

    @staticmethod
    def cosine_score(embedding1: list[float], embedding2: list[float]) -> float:
        """
        Calculate the cosine similarity score between two embeddings.

        Args:
            embedding1 (array-like): The first embedding vector.
            embedding2 (array-like): The second embedding vector.

        Returns:
            float: The cosine similarity score between the two embeddings.
        """
        return dot(embedding1, embedding2) / (norm(embedding1) * norm(embedding2))

    def compare_embeddings(self, text_embeddings: list[list[float]]) -> list[str]:
        """
        Find the name of the entry with the closest cosine similarity for each input text embedding.

        Args:
            text_embeddings (list[array-like]): The list of input text embeddings to compare.

        Returns:
            list[str]: The names of the closest entries for each text embedding.
        """
        closest_names = []

        for text_embedding in text_embeddings:
            highest_score = -1
            closest_name = None

            for entry in self.entries:
                score = self.cosine_score(text_embedding, entry["embedding"])
                if score > highest_score:
                    highest_score = score
                    closest_name = entry["name"]

            closest_names.append(closest_name)

        return closest_names
