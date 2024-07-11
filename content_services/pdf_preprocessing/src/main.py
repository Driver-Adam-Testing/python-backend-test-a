import json
import os
from datetime import datetime
from uuid import UUID
import fitz
import requests
from openai import OpenAI
from pydantic import BaseModel
from sqlalchemy import JSON, String
from config import settings
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from urllib.parse import urlparse
from database.models_v1 import (
    Chunk,
    Codebase,
    ContentMetadata,
    ContentType,
    Llm,
    DerivedContent,
    SourceContent, DerivedContentType,
)
from sqlmodel import select

from embed_helpers import generate_embeddings_for_string

LLM_MODEL = "gpt-4o"

client = OpenAI(
    # This is the default and can be omitted
    api_key=settings.OPENAI_API_KEY,
)


def download_pdf(presigned_url, download_path):
    response = requests.get(presigned_url)
    with open(download_path, 'wb') as file:
        file.write(response.content)
    return download_path


def split_pdf_into_pages(pdf_path):
    doc = fitz.open(pdf_path)
    pages = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        images = page.get_images(full=True)
        pages.append({
            'page_num': page_num + 1,
            'text': text,
            'images': images
        })
    return pages


def summarize_text_with_openai(text):
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
    entire_text = "\n\n".join([page['text'] for page in pages])
    pdf_summary = summarize_text_with_openai(entire_text)

    page_summaries = []
    with ThreadPoolExecutor() as executor:
        future_to_page = {executor.submit(summarize_text_with_openai, page['text']): page for page in pages}
        for future in as_completed(future_to_page):
            page = future_to_page[future]
            try:
                summary = future.result()
                print(f"Page {page['page_num']} Summary: {summary}")
                page_summaries.append({
                    'page_num': page['page_num'],
                    'summary': summary
                })
            except Exception as exc:
                print(f"Page {page['page_num']} generated an exception: {exc}")
                page_summaries.append({
                    'page_num': page['page_num'],
                    'summary': "Error: Could not generate summary."
                })

    # Ensure all pages are summarized
    summarized_pages = {summary['page_num'] for summary in page_summaries}
    for page in pages:
        if page['page_num'] not in summarized_pages:
            page_summaries.append({
                'page_num': page['page_num'],
                'summary': "Error: Summary missing."
            })

    # Sort page summaries by page number
    page_summaries.sort(key=lambda x: x['page_num'])

    return pdf_summary, page_summaries


# get source content by source_content_id
async def get_source_content(source_content_id: UUID, session) -> SourceContent:
    from sqlmodel import select
    sc = await session.exec(select(SourceContent).where(SourceContent.id == source_content_id))
    return sc.first()


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


async def get_llm_uuid(llmModel: str, session) -> UUID:
    from sqlmodel import select

    llm_uuid = None
    sel_statement = select(Llm).where(
        Llm.model == llmModel
    )
    llm_dct = (await session.exec(sel_statement)).first()
    if llm_dct:
        llm_uuid = llm_dct.id
    return llm_uuid


async def create_source_content(workspace_id, codebase_id, source_content_type_id, session) -> SourceContent:
    from sqlmodel import insert
    source_content = SourceContent(
        workspace_id=workspace_id,
        codebase_id=codebase_id,
        source_content_type_id=source_content_type_id
    )
    session.add(source_content)
    await session.commit()
    return source_content


async def create_derived_content(source_content, pdf_summary, page_summaries, session) -> [DerivedContent]:
    from sqlmodel import insert
    derived_contents = []
    # Placeholder for creating derived content
    derived_content_type_id = await get_derived_content_type_uuid('pdf_summary', session)
    llm_uuid = await get_llm_uuid(LLM_MODEL, session)

    derived_contents.append(DerivedContent(
        source_content_id=source_content.id,
        derived_content_type_id=derived_content_type_id,
        content=pdf_summary,
        status="generation-complete",
        llm_id=llm_uuid,
        order=0
    ))

    for page_summary in page_summaries:
        page_summary_dc = DerivedContent(
            source_content_id=source_content.id,
            derived_content_type_id=derived_content_type_id,
            content=page_summary['summary'],
            status="generation-complete",
            llm_id=llm_uuid,
            metadata={
                'page_num': page_summary['page_num']
            },
            order=page_summary['page_num']
        )
        derived_contents.append(page_summary_dc)

    return derived_contents


def create_content_metadata(pdf_summary, page_summaries):
    content_metadata = {
        'pdf_summary': pdf_summary,
        'page_summaries': page_summaries
    }
    return content_metadata


async def persist_embeddings(
        session,
        split_documents: list,
        embeds: list,
        content_type: ContentType,
        codebase_id: str,
        workspace_id: str,
        relative_path: str,
        metadata: dict = {},
) -> bool:
    from sqlmodel import delete, select

    if len(split_documents) > 0:
        try:
            query = (
                select(ContentMetadata)
                .where(ContentMetadata.codebase_id == codebase_id)
                .where(ContentMetadata.relative_path == relative_path)
                .where(ContentMetadata.content_type == content_type)
                .where(ContentMetadata.workspace_id == workspace_id)
            )

            if 'document-type' in metadata:
                query = query.where(
                    ContentMetadata.misc_metadata["document-type"].as_string() == content_type
                )

            if 'page_num' in metadata:
                page_num = str(metadata['page_num'])
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
                    updated_at=datetime.now()
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
                for i, (d, e) in enumerate(zip(split_documents, embeds))
            ]
            return True
        except Exception as e:
            print(f"Error embedding {relative_path}: {e}")
            return False
    else:
        return True


class PdfInput(BaseModel):
    presigned_url: str
    pdf_name: str | None = None
    source_content_id: str | None = None


async def preprocess(input: PdfInput):
    presigned_url = input.presigned_url
    source_content_id = input.source_content_id
    pdf_name = input.pdf_name or os.path.basename(urlparse(presigned_url).path)
    download_path = f'./pdfs/{pdf_name}'
    # Download the PDF
    pdf_path = download_pdf(presigned_url, download_path)
    # Split PDF into pages
    pages = split_pdf_into_pages(pdf_path)
    # Summarize the PDF and its pages
    pdf_summary, page_summaries = summarize_pdf_content(pages)
    # pdf_summary = "some pdf summary"
    # page_summaries = [{'page_num': 1,
    #                    'summary': 'This configuration pertains to an HTTPS load balancer setup with distinct rules and target groups. Here’s a detailed technical summary:\n\n### Listeners\n1. **Protocol and Port**: Listens on HTTPS (secured HTTP) on port 443.\n\n### Rules\n1. **Rule 1**: \n   - **Priority**: 100\n   - **Action**: Forward traffic to a specified target group.\n   - **Conditions**: Applies if the URL path pattern matches `/*` (all requests).\n\n2. **Rule 2** (Default rule):\n   - **Action**: Return a fixed response if no other rule matches.\n   - **Condition**: Applies when no other rule is satisfied.\n\n### Target Group (DLMApiTargetGroup)\n- The target group contains two targets with specific IP addresses and health statuses.\n- **Algorithm**: Likely round-robin or similar distribution mechanism (implied but not specified).\n\n### Targets\n1. **Target 1**:\n   - **Port**: 4000\n   - **IP Address**: 172.10.144.25\n   - **Status**: Healthy\n\n2. **Target 2**:\n   - **Port**: 4000\n   - **IP Address**: 172.10.209.196\n   - **Status**: Healthy\n\n### Summary\n- **HTTPS Listener** on port 443 with a forwarding rule having the highest priority (100) to a target group if the path pattern matches `/*`.\n- **Default rule** to handle all unmatched requests with a fixed response.\n- **Target Group "DLMApiTargetGroup"**: Contains 2 healthy targets listening on port 4000, addressed at 172.10.144.25 and 172.10.209.196 respectively.\n\nThis setup ensures that all incoming HTTPS traffic is routed primarily to the healthy backend targets provided, with a catch-all rule to handle any unmatched requests.'}]
    from database.db import async_engine
    from sqlmodel.ext.asyncio.session import AsyncSession
    async with AsyncSession(async_engine) as session:
        async with session.begin():
            # Get source content
            source_content = await get_source_content(UUID(source_content_id), session)
            # Create derived content
            derived_content_records = await create_derived_content(source_content, pdf_summary, page_summaries, session)
            session.add_all(derived_content_records)
            # await session.commit()

            for derived_content in derived_content_records:
                # Generate embeddings   
                split_documents, embeds = await generate_embeddings_for_string(derived_content.content)
                # TODO replace with content type
                await persist_embeddings(session,
                                         split_documents,
                                         embeds,
                                         ContentType.PDF_SUMMARY,
                                         str(source_content.codebase_id),
                                         str(source_content.workspace_id),
                                         source_content.relative_path,
                                         {'document-type': ContentType.PDF_SUMMARY,
                                          'page_num': derived_content.order})

                # Create content metadata
            content_metadata = create_content_metadata(pdf_summary, page_summaries)

            await session.commit()

    with open(f'./metadata/{pdf_name}_metadata.json', 'w') as json_file:
        json.dump(content_metadata, json_file, indent=4)
    return content_metadata
