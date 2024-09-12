import os

import modal

app = modal.App("pdf-summary-embedding")

image_jve = (
    modal.Image.debian_slim(python_version="3.12")
    .copy_local_dir("../../driver_db/", remote_path="/driver_db")
    .copy_local_dir(local_path="../../packages/shared", remote_path="/packages/shared")
    .poetry_install_from_file("pyproject.toml")
    .apt_install("default-jre")
)

pdf_preprocessing_modal_config = {
    "image": image_jve,
    "mounts": [
        modal.Mount.from_local_dir(
            local_path="../../driver_db/certs",
            remote_path="/root/data/",
        ),
    ],
    "secrets": [
        modal.Secret.from_name("driver-api-credentials"),
        modal.Secret.from_name("open-ai"),
        modal.Secret.from_name("db"),
        modal.Secret.from_name("aws-inspector-s3"),
    ],
    "proxy": modal.Proxy.from_name("pg-proxy")
    if os.environ["MODAL_ENVIRONMENT"] != "staging"
    else None,
    "concurrency_limit": 5,
    "region": "us-east",
}


@app.function(timeout=3600, **pdf_preprocessing_modal_config)
def create_and_embed_pdf_summaries(content_id) -> None:
    import io

    import requests
    from database.db import engine
    from database.models_v1 import ChunkAndEmbedding, DerivedContent, DerivedContentType
    from shared.chunking.text_splitter import split_text
    from shared.embedding.text_embedder import batch_embed_text
    from shared.file_storage.s3 import get_presigned_url_from_content_information
    from shared.pipelines.process_file.process_file_pdf import run_process_pdf
    from sqlalchemy.orm import selectinload
    from sqlmodel import Session, select

    # TODO: call an orm function to do this.
    with Session(engine) as session:
        content_results = session.exec(
            select(DerivedContent)
            .where(DerivedContent.id == content_id)
            .options(selectinload(DerivedContent.workspace))
        ).all()
        if len(content_results) != 1:
            raise Exception("Wrong content_id value")
        content: DerivedContent = content_results[0]

        presigned_url = get_presigned_url_from_content_information(
            codebase_id=content.codebase_id,
            organization_id=content.workspace.organization_id,
            relative_path=content.relative_path,
        )

    response = requests.get(presigned_url)
    response.raise_for_status()

    pdf_content = io.BytesIO(response.content)
    pdf_content.name = content.relative_path.split("/")[-1]
    results = run_process_pdf(pdf_content)
    with Session(engine) as session:
        for result in results:
            content_type_id = session.exec(
                select(DerivedContentType.id).where(
                    DerivedContentType.type_name == result.content_type.value
                )
            ).one_or_none()

            if content_type_id is None:
                raise Exception(
                    f"DerivedContentType not found for value: {result.content_type.value}"
                )

            # TODO: This should all be in a service.

            derived_content = DerivedContent(
                workspace_id=content.workspace.id,
                codebase_id=content.codebase_id,
                content=result.content,
                content_type_id=content_type_id,
                source_content_id=content_id,
                misc_metadata={
                    "open_ai_file_id": result.open_ai_file_id,
                    "page": result.page,
                },
                relative_path=content.relative_path,
            )
            session.add(derived_content)
            session.commit()
            session.refresh(derived_content)
            splits = split_text(result.content)
            try:
                embeds = batch_embed_text(splits)
                for i, split in enumerate(splits):
                    session.add(
                        ChunkAndEmbedding(
                            content_id=derived_content.id,
                            text=split.text,
                            chunk_number=i,
                            text_embedding_3_small=embeds[i],
                        )
                    )
            except Exception as e:
                print(e)
                # sEnd a n email here
            session.commit()

    return results
