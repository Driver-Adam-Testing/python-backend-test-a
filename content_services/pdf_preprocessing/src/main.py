import hashlib
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

import modal
import requests
from config import settings
from database.models_v1 import (
    Chunk,
    ContentMetadata,
    ContentType,
    DerivedContent,
    DerivedContentType,
)
from embed_helpers import generate_embeddings_for_string
from utils.aws_s3 import generate_get_presigned_url

LLM_MODEL = "gpt-4o"

app = modal.App("pdf-summary-embedding")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .copy_local_dir("../../driver_db/", remote_path="/driver_db")
    .poetry_install_from_file("pyproject.toml")
)


def download_pdf(presigned_url, download_path):
    response = requests.get(presigned_url)
    with open(download_path, "wb") as file:
        file.write(response.content)
    return download_path


def split_pdf_into_pages(pdf_path):
    import pymupdf as fitz

    doc = fitz.open(pdf_path)
    pages = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        images = page.get_images(full=True)
        pages.append({"page_num": page_num + 1, "text": text, "images": images})
    return pages


def summarize_text_with_openai(text):
    from openai import OpenAI

    client = OpenAI(
        # This is the default and can be omitted
        api_key=settings.OPENAI_API_KEY,
    )
    PROMPT = f"I am a seasoned software engineer, I seek in-depth technical summarization of text:\n\n{text}"
    MESSAGE = {"role": "user", "content": PROMPT}
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            MESSAGE,
        ],
        model=LLM_MODEL,
    )
    return chat_completion.choices[0].message.content


def summarize_pdf_content(pages):
    entire_text = "\n\n".join([page["text"] for page in pages])
    pdf_summary = summarize_text_with_openai(entire_text)

    page_summaries = []
    with ThreadPoolExecutor() as executor:
        future_to_page = {
            executor.submit(summarize_text_with_openai, page["text"]): page
            for page in pages
        }
        for future in as_completed(future_to_page):
            page = future_to_page[future]
            try:
                summary = future.result()
                print(f"Page {page['page_num']} Summary: {summary}")
                page_summaries.append(
                    {"page_num": page["page_num"], "summary": summary}
                )
            except Exception as exc:
                print(f"Page {page['page_num']} generated an exception: {exc}")
                page_summaries.append(
                    {
                        "page_num": page["page_num"],
                        "summary": "Error: Could not generate summary.",
                    }
                )

    # Ensure all pages are summarized
    summarized_pages = {summary["page_num"] for summary in page_summaries}
    for page in pages:
        if page["page_num"] not in summarized_pages:
            page_summaries.append(
                {"page_num": page["page_num"], "summary": "Error: Summary missing."}
            )

    # Sort page summaries by page number
    page_summaries.sort(key=lambda x: x["page_num"])

    return pdf_summary, page_summaries


# TODO dedup
async def get_source_content(source_content_id: UUID, session) -> DerivedContent:
    from database.models_v1 import Workspace  # Import Workspace model
    from sqlmodel import select

    query = (
        select(DerivedContent, Workspace)
        .join(Workspace, DerivedContent.workspace_id == Workspace.id)
        .where(DerivedContent.id == source_content_id)
    )
    result = await session.exec(query)
    source_content, workspace = result.first()
    source_content.workspace = workspace  # Attach workspace to source_content
    return source_content


async def get_derived_content_type_uuid(content_type: str, session) -> UUID:
    from sqlmodel import select

    dct_uuid = None
    sel_statement = select(DerivedContentType).where(
        DerivedContentType.type_name == content_type
    )
    res_dct = (await session.exec(sel_statement)).first()
    if res_dct:
        dct_uuid = res_dct.id
    return dct_uuid


async def create_derived_content_without_inserting(
    source_content, pdf_summary, page_summaries, session
) -> [DerivedContent]:
    derived_contents = []
    # Placeholder for creating derived content
    content_type_id = await get_derived_content_type_uuid("pdf_summary", session)

    derived_contents.append(
        DerivedContent(
            relative_path=source_content.relative_path,
            source_content_id=source_content.id,
            content_type_id=content_type_id,
            content=pdf_summary,
            status="generation-complete",
            order=0,
        )
    )

    for page_summary in page_summaries:
        page_summary_dc = DerivedContent(
            relative_path=source_content.relative_path,
            source_content_id=source_content.id,
            content_type_id=content_type_id,
            content=page_summary["summary"],
            status="generation-complete",
            metadata={"page_num": page_summary["page_num"]},
            order=page_summary["page_num"],
        )
        derived_contents.append(page_summary_dc)

    return derived_contents


def create_content_metadata(pdf_summary, page_summaries):
    content_metadata = {"pdf_summary": pdf_summary, "page_summaries": page_summaries}
    return content_metadata


async def persist_embeddings(
    session,
    split_documents: list,
    embeds: list,
    content_type: ContentType,
    codebase_id: str,
    workspace_id: str,
    relative_path: str,
    metadata: dict | None = None,
) -> bool:
    from sqlmodel import delete, select

    metadata = metadata or {}

    if len(split_documents) > 0:
        try:
            query = (
                select(ContentMetadata)
                .where(ContentMetadata.codebase_id == codebase_id)
                .where(ContentMetadata.relative_path == relative_path)
                .where(ContentMetadata.content_type == content_type)
                .where(ContentMetadata.workspace_id == workspace_id)
            )

            if "document-type" in metadata:
                query = query.where(
                    ContentMetadata.misc_metadata["document-type"].as_string()
                    == content_type
                )

            if "page_num" in metadata:
                page_num = str(metadata["page_num"])
                query = query.where(
                    ContentMetadata.misc_metadata["page_num"].as_string() == page_num
                )

            cm_res = await session.exec(query)
            cm = cm_res.first()
            if cm is not None:
                # Delete existing chunks associated with cm
                print("existing metadata: ", cm.relative_path, cm.content_type)
                await session.exec(
                    delete(Chunk).where(Chunk.content_metadata_id == cm.id)
                )
                cm.misc_metadata = metadata
            else:
                cm = ContentMetadata(
                    workspace_id=workspace_id,
                    misc_metadata=metadata,
                    content_type=content_type,
                    relative_path=relative_path,
                    codebase_id=codebase_id,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                print("creating: ", relative_path, content_type)

            session.add(cm)
            line_number = 0
            # if content_type == ContentType.CODE_SYMBOL and "line" in metadata:
            #     line_number = metadata["line"]
            [
                session.add(
                    Chunk(
                        text_embedding_3_small=e,
                        text=d.text,
                        content_metadata_id=cm.id,
                        chunk_number=i,
                        token_count=len(d.tokens),
                        line_number=line_number if line_number != 0 else d.start_line,
                    )
                )
                for i, (d, e) in enumerate(zip(split_documents, embeds, strict=False))
            ]
            return True
        except Exception as e:
            print(f"Error embedding {relative_path}: {e}")
            return False
    else:
        return True


# TODO: consolidate all embeddings into one place / service
# TODO: Replace pre-signed url with boto3 impl.


# async def preprocess(input: PdfInput):
async def preprocess(source_content_id: str):
    from database.db import async_engine
    from sqlmodel.ext.asyncio.session import AsyncSession

    async with AsyncSession(async_engine) as session:
        async with session.begin():
            source_content = await get_source_content(UUID(source_content_id), session)
            org_id = source_content.workspace.organization_id
            org_id_hash = hashlib.sha256(org_id.encode()).hexdigest()[:63]

            object_key = f"{source_content.codebase_id}/{source_content.relative_path}"
            presigned_url = generate_get_presigned_url(
                key=object_key, bucket=org_id_hash
            )

            pdf_name = os.path.basename(urlparse(source_content.relative_path).path)
            download_path = Path(pdf_name)

            pdf_path = download_pdf(presigned_url, download_path)
            pages = split_pdf_into_pages(pdf_path)
            pdf_summary, page_summaries = summarize_pdf_content(pages)
            derived_content_records = await create_derived_content_without_inserting(
                source_content, pdf_summary, page_summaries, session
            )
            session.add_all(derived_content_records)
            embedding_dict = {}
            for derived_content in derived_content_records:
                # Generate embeddings
                split_documents, embeds = await generate_embeddings_for_string(
                    derived_content.content
                )

                content_embedded = await persist_embeddings(
                    session,
                    split_documents,
                    embeds,
                    ContentType.PDF_SUMMARY,
                    str(source_content.codebase_id),
                    str(source_content.workspace_id),
                    source_content.relative_path,
                    {
                        "document-type": ContentType.PDF_SUMMARY,
                        "page_num": derived_content.order,
                    },
                )
                embedding_dict[derived_content.id] = content_embedded

            await session.commit()

            for key, value in embedding_dict.items():
                print(f"Embedding for {key} persisted: {value}")
    return


@app.function(
    image=image,
    mounts=[
        modal.Mount.from_local_python_packages("database"),
        modal.Mount.from_local_dir(
            local_path="../../driver_db/certs/",
            remote_path="/root/data/",
        ),
    ],
    secrets=[
        modal.Secret.from_name("env-name"),
        modal.Secret.from_name("aws-inspector-s3"),
        modal.Secret.from_name("db"),
        modal.Secret.from_name("open-ai"),
    ],
    proxy=modal.Proxy.from_name("pg-proxy"),
    timeout=24 * 60 * 60,
    region="us-east",
    concurrency_limit=5,
)
async def create_and_embed_pdf_summaries(source_content_id: str) -> None:
    # add some logging
    print("Starting PDF preprocessing...")
    print(f"Creating summaries for source_content: {source_content_id}")
    if not source_content_id:
        raise ValueError("source_content_id is required")

    await preprocess(source_content_id)


async def run_tasks():
    import asyncio

    source_content_ids = [
        "106856ea-3f7c-476a-ac4f-35d77358e8c1",
        "37741946-00d8-4be0-bd89-9515e17da734",
        "c7a53985-2c10-4211-b738-15e1a9b4bb70",
        "80e0d455-5c62-467b-9b7e-db78ddf5e160",
        "7271b7c7-733a-4f8f-b65c-e281485fe2b8",
        "e50abaca-14f8-4af8-b6ef-933cd0c599f6",
        "e5d4e2c8-9a44-43f4-a355-b300d539889b",
        "c25452a8-e8b5-42df-89d5-d024557588d4",
        "e5266a3a-1232-4665-a871-7f1bb2b356d7",
        "a6dd3cab-adc6-46fc-8f5e-e9b01b8f3eef",
        "fa904fac-74be-4143-836c-59dcf293cb7c",
        "e81caf63-95bd-4f34-b84f-0f750df1da40",
    ]
    tasks = [
        create_and_embed_pdf_summaries.remote(source_content_id)
        for source_content_id in source_content_ids
    ]
    await asyncio.gather(*tasks)


@app.local_entrypoint()
def main():
    import asyncio

    asyncio.run(run_tasks())
