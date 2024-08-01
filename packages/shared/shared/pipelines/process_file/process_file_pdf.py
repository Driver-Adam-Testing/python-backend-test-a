import io
import os

import fitz
from openai import OpenAI

from shared.agent.models.openai.file_search import query_file
from shared.interfaces.file_content.pdf_file_content import (
    ProcessedPdfFileContent,
    ProcessedPdfFileContentType,
)
from shared.utils.openai_file import upload_file_to_open_ai

client = OpenAI()

assistant = client.beta.assistants.create(
    name="PDF Summarizer",
    instructions="You are an expert microprocessors and hardware engineer, as well as a technical writer.",
    model="gpt-4o",
    tools=[{"type": "file_search"}],
)


def run_process_pdf(file_content: io.BytesIO) -> list[ProcessedPdfFileContent]:
    summarization_query = "Summarize the uploaded file. Be verbose and descriptive. If the pdf has diagrams, schematics, images, text, or tables, describe them in great detail."
    processed_contents = []
    file_id = upload_file_to_open_ai(file_content)
    whole_file_summary = query_file(
        query=summarization_query, file_id=file_id, assistant_id=assistant.id
    )

    summarization_query += f" <context>This file is part of a larger context, described here: {whole_file_summary} </context>  If there is an electrical schematic, describe all connections and features of the diagram.  If there is a chart, describe the type of chart and the values it depicts."
    processed_contents.append(
        ProcessedPdfFileContent(
            content=whole_file_summary,
            content_type=ProcessedPdfFileContentType.VISUAL_SUMMARY,
            open_ai_file_id=file_id,
        )
    )

    pages = split_pdf_into_pages(file_content=file_content)

    for index, page_content in enumerate(pages):
        print(f"Processing page {index + 1}")
        page_file_id = upload_file_to_open_ai(page_content)

        processed_contents.append(
            ProcessedPdfFileContent(
                content=query_file(
                    file_id=page_file_id,
                    query=summarization_query,
                    assistant_id=assistant.id,
                ),
                page=index + 1,
                content_type=ProcessedPdfFileContentType.VISUAL_SUMMARY,
                open_ai_file_id=page_file_id,
            )
        )
        processed_contents.append(
            ProcessedPdfFileContent(
                content=extract_text_from_pdf(page_content),
                page=index + 1,
                content_type=ProcessedPdfFileContentType.EXTRACTED_TEXT,
                open_ai_file_id=page_file_id,
            )
        )
        for table in extract_tables_from_pdf(page_content):
            processed_contents.append(
                ProcessedPdfFileContent(
                    content=str(table),
                    page=index + 1,
                    content_type=ProcessedPdfFileContentType.EXTRACTED_TABLE,
                )
            )
        for image in extract_images_from_pdf(page_content):
            image_file_id = upload_file_to_open_ai(image)
            processed_contents.append(
                ProcessedPdfFileContent(
                    content=query_file(
                        file_id=image_file_id,
                        query=summarization_query,
                        assistant_id=assistant.id,
                    ),
                    page=index + 1,
                    content_type=ProcessedPdfFileContentType.EXTRACTED_IMAGE_SUMMARY,
                    open_ai_file_id=image_file_id,
                )
            )
    return processed_contents


def split_pdf_into_pages(file_content: io.BytesIO):
    pdf_document = fitz.open(stream=file_content, filetype="pdf")

    created_pages = []
    for page_num in range(len(pdf_document)):
        single_page_pdf = fitz.open()
        single_page_pdf.insert_pdf(pdf_document, from_page=page_num, to_page=page_num)
        page_bytes_io = io.BytesIO()
        single_page_pdf.save(page_bytes_io)
        page_bytes_io.seek(0)
        page_bytes_io.name = (
            f"{os.path.splitext(file_content.name)[0]}_page_{page_num + 1}.pdf"
        )
        created_pages.append(page_bytes_io)
    return created_pages


def extract_text_from_pdf(file_content: io.BytesIO):
    pdf_document = fitz.open(stream=file_content, filetype="pdf")

    all_text = ""
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        all_text += page.get_text()

    return all_text


def extract_images_from_pdf(file_content: io.BytesIO):
    pdf_document = fitz.open(stream=file_content, filetype="pdf")

    images = []
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_filename = f"{os.path.splitext(file_content.name)[0]}_img_{img_index + 1}.{image_ext}"
            image_bytes_io = io.BytesIO(image_bytes)
            image_bytes_io.name = image_filename
            images.append(image_bytes_io)

    return images


def extract_tables_from_pdf(file_content: io.BytesIO):
    # TODO: Tabula requires a JVM
    import tabula

    tables = tabula.read_pdf(file_content, pages="all", multiple_tables=True)
    if tables:
        return tables
    else:
        return []
