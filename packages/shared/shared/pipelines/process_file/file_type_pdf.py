import io
import os

import fitz
from openai import OpenAI

from shared.interfaces.file_content.pdf_file_content import (
    ProcessedPdfFileContent,
    ProcessedPdfFileContentType,
)

client = OpenAI()

assistant = client.beta.assistants.create(
    name="PDF Summarizer",
    instructions="You are a microprocessors and hardware expert engineer, as well as a technical writer.",
    model="gpt-4o",
    tools=[{"type": "file_search"}],
)


def run_process_pdf(file_content: io.BytesIO) -> list[ProcessedPdfFileContent]:
    processed_contents = []
    file_id = upload_file_to_open_ai(file_content)
    whole_file_summary = summarize_file(file_id=file_id)
    processed_contents.append(
        ProcessedPdfFileContent(
            content=whole_file_summary,
            content_type=ProcessedPdfFileContentType.VISUAL_SUMMARY,
            open_ai_file_id=file_id,
        )
    )

    pages = split_pdf_into_individual_pages(file_content=file_content)

    for index, page_content in enumerate(pages):
        print(f"Processing page {index + 1}")
        page_file_id = upload_file_to_open_ai(page_content)

        processed_contents.append(
            ProcessedPdfFileContent(
                content=summarize_file(
                    file_id=page_file_id, context=whole_file_summary
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
            image_content = image[1]
            image_file_bytes_io = io.BytesIO(image_content)
            image_file_bytes_io.name = image[0]
            image_file_id = upload_file_to_open_ai(image_file_bytes_io)

            image_summary = summarize_file(file_id=image_file_id)
            processed_contents.append(
                ProcessedPdfFileContent(
                    content=image_summary,
                    page=index + 1,
                    content_type=ProcessedPdfFileContentType.EXTRACTED_IMAGE_SUMMARY,
                    open_ai_file_id=image_file_id,
                )
            )
    return processed_contents


def split_pdf_into_individual_pages(file_content: io.BytesIO):
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
            images.append((image_filename, image_bytes))

    return images


def upload_file_to_open_ai(file_content: io.BytesIO):
    message_file = client.files.create(file=file_content, purpose="assistants")
    return message_file.id


def summarize_file(file_id, context=None):
    query = "Summarize the uploaded file. Be verbose and descriptive. If the pdf has diagrams, schematics, images, text, or tables, describe them in great detail."
    if context:
        query += f" <context>This file is part of a larger context, described here: {context} </context>  If there is an electrical schematic, describe all connections and features of the diagram.  If there is a chart, describe the type of chart and the values it depicts."

    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": query,
                "attachments": [
                    {"file_id": file_id, "tools": [{"type": "file_search"}]}
                ],
            }
        ]
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        instructions="You're an expert technical writer and engineer who can understand technical documents.",
        assistant_id=assistant.id,
    )

    if run.status == "completed":
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        summary = messages.data[0].content[0].text.value
        return summary


def extract_tables_from_pdf(file_content: io.BytesIO):
    # TODO: Tabula requires a JVM
    import tabula

    tables = tabula.read_pdf(file_content, pages="all", multiple_tables=True)
    if tables:
        return tables
    else:
        return []
