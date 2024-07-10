import time
from text_embedder import TextEmbedder
from text_splitter import TextSplitter


async def generate_embeddings_for_string(content: str) -> tuple[list, list]:
    text_splitter = TextSplitter()
    text_embedder = TextEmbedder()
    split_documents = text_splitter.split(content)

    if len(split_documents) > 0:
        max_retries = 10
        for attempt in range(max_retries):
            try:
                embeds = text_embedder.batch_embed_text(
                    [d.text for d in split_documents]
                )
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(
                        f"Failed to embed, retrying {attempt + 1}/{max_retries} in 0.5s"
                    )
                    time.sleep(0.5)
                    print(e)
                else:
                    print(f"Failed to embed after {max_retries} attempts.")
                    raise e
        return split_documents, embeds

    return [], []
