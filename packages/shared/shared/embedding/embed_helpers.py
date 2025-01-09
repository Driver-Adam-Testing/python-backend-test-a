import time
from pathlib import Path

from shared.chunking.text_splitter import split_text
from shared.embedding.text_embedder import async_batch_embed_text


def download_source_content_file(
    s3_client: any,
    codebase_storage_url: str,
    codebase_root: str,
    source_content_rel_path: str,
    download_root: Path,
) -> Path:
    parsed_url = codebase_storage_url.replace("https://", "").split("/")
    bucket_name = parsed_url[0].split(".")[
        0
    ]  # Extract the bucket name from the URL... fragile
    s3_key = "/".join(parsed_url[1:]) + f"/source/{source_content_rel_path}"
    local_download_path = download_root / source_content_rel_path
    local_download_path.parent.mkdir(parents=True, exist_ok=True)

    # print("Bucket name:", bucket_name)
    # print("S3 key:", s3_key)
    # print("Local download path:", local_download_path)
    s3_client.download_file(bucket_name, s3_key, str(local_download_path))
    print(f"File downloaded to {local_download_path}")
    return local_download_path


async def generate_embeddings_for_string(content: str) -> tuple[list, list]:
    split_documents = split_text(content)

    if len(split_documents) > 0:
        max_retries = 10
        for attempt in range(max_retries):
            try:
                embeds = await async_batch_embed_text([d.text for d in split_documents])
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
