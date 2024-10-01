import base64
import concurrent.futures
import io
import os
import time
from io import BytesIO

import anthropic
import fitz
from openai import OpenAI
from PIL import Image

from shared.agent.models.openai.file_search import query_file
from shared.interfaces.file_content.pdf_file_content import (
    ProcessedPdfFileContent,
    ProcessedPdfFileContentType,
)
from shared.utils.openai_file import upload_file_to_open_ai

client = OpenAI()
print()

SUMMARIZE_PDF_PROMPT = """Analyze the provided PDF file and summarize its contents. The file may contain technical documentation, but it could also include other types of content. Your task is to perform an analysis and provide a summary.

If the information is available:

High-Level Overview:

What is the main focus of the document? Summarize the key themes, topics, and objectives.
Identify any overarching purpose or intent behind the document.
When applicable, provide descriptions of each:

Text & Topics: List the main topics discussed in the document. Describe key themes, terms, and concepts in detail.
Sections & Headers: Enumerate and describe  sections, sub-sections, headers, and sub-headers. Include a breakdown of their contents where applicable.
Images, Diagrams, and Schematics: Describe all visual content in the document, including diagrams, charts, graphs, tables, and schematics. Explain the purpose and content of these visuals in detail.
Tables: If tables are present, summarize the data or information presented in each table.

If the document cannot be accessed, if you cannot search it, or if no meaningful information is available, return only the text: ERROR"""


DESCRIBE_IMAGE_PROMPT = """
Describe the image in detail without asking any follow-up questions.
For photographs or artwork, provide a general description of the scene, subjects, colors, and notable elements.
For diagrams, charts, or technical illustrations:

Specify the type (e.g. flowchart, bar graph, schematic)
Describe the overall layout and structure
List and explain all labeled components or sections
Detail any arrows, lines, or connections between elements
Note any color coding or visual hierarchies
Describe any numerical data, scales, or units present
Explain the title, legend, and any captions
Summarize the main information or process being conveyed

For all images, include any text visible in the image verbatim. Point out any unusual or striking visual elements. Provide a comprehensive description without requesting clarification or additional information.
"""
assistant = client.beta.assistants.create(
    name="PDF Summarizer",
    instructions="You are an expert microprocessors and hardware engineer, as well as a technical writer.",
    model="gpt-4o-mini-2024-07-18",
    tools=[{"type": "file_search"}, {"type": "code_interpreter"}],
)


def summarize_pdf_with_retry(
    file_content: io.BytesIO, summarization_query: str, assistant_id: str
) -> str:
    attempts = 3
    file_id = upload_file_to_open_ai(file_content)
    for attempt in range(attempts):
        try:
            whole_file_summary = query_file(
                file_id=file_id, query=summarization_query, assistant_id=assistant_id
            )
            print(whole_file_summary)
            print(file_id)
            print(assistant_id)
            if whole_file_summary != "ERROR":
                return whole_file_summary
        except Exception as e:
            print(e)
            if attempt < attempts - 1:
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in 30 seconds...")
                time.sleep(10)
            else:
                print(f"All {attempts} attempts failed: {e}")
                print("Attempting image upload")
                try:
                    return summarize_images(
                        pdf_page_to_image(file_content=file_content)
                    )
                except Exception as e:
                    raise e


def summarize_images(images: list[io.BytesIO], prompt: str | None) -> str:
    encoded_images = []
    for image in images:
        image_data = base64.b64encode(image.read()).decode("utf-8")
        file_extension = image.name.split(".")[-1].lower()

        if file_extension == "jpeg" or file_extension == "jpg":
            image_media_type = "image/jpeg"
        elif file_extension == "png":
            image_media_type = "image/png"
        elif file_extension == "gif":
            image_media_type = "image/gif"
        elif file_extension == "webp":
            image_media_type = "image/webp"
        else:
            raise ValueError(f"Unsupported image type: {file_extension}")

        encoded_images.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image_media_type,
                    "data": image_data,
                },
            }
        )

    encoded_images.append(
        {"type": "text", "text": prompt if prompt is not None else SUMMARIZE_PDF_PROMPT}
    )

    message = anthropic.Anthropic().messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": encoded_images,
            }
        ],
    )
    return str(message.content[0].text)


def process_visual_summary(
    page_content: io.BytesIO,
    index: int,
    summarization_query: str,
    assistant_id: str | None,
) -> None | ProcessedPdfFileContent:
    try:
        # TODO: perhaps all of these parallel methods could be simpler.
        return ProcessedPdfFileContent(
            content=summarize_pdf_with_retry(
                page_content, summarization_query, assistant_id
            ),
            page=index + 1,
            content_type=ProcessedPdfFileContentType.VISUAL_SUMMARY,
        )
    except Exception:
        return None


def process_extracted_text(
    page_content: BytesIO, index: int
) -> ProcessedPdfFileContent:
    return ProcessedPdfFileContent(
        content=extract_text_from_pdf(page_content),
        page=index + 1,
        content_type=ProcessedPdfFileContentType.EXTRACTED_TEXT,
    )


def process_extracted_tables(
    page_content: BytesIO, index: int
) -> list[ProcessedPdfFileContent]:
    table_contents = []
    for table in extract_tables_from_pdf(page_content):
        table_contents.append(
            ProcessedPdfFileContent(
                content=str(table),
                page=index + 1,
                content_type=ProcessedPdfFileContentType.EXTRACTED_TABLE,
            )
        )
    return table_contents


def process_image(image: io.BytesIO, index: int) -> ProcessedPdfFileContent:
    try:
        image_summary = summarize_images([image], prompt=DESCRIBE_IMAGE_PROMPT)
        return ProcessedPdfFileContent(
            content=image_summary,
            page=index + 1,
            content_type=ProcessedPdfFileContentType.EXTRACTED_IMAGE_SUMMARY,
        )
    except Exception as e:
        print(f"An error occurred while processing the image on page {index + 1}: {e}")
        return None


def run_process_pdf(file_content: io.BytesIO) -> list[ProcessedPdfFileContent]:
    processed_contents = []
    whole_file_summary = summarize_pdf_with_retry(
        file_content, SUMMARIZE_PDF_PROMPT, assistant.id
    )
    processed_contents.append(
        ProcessedPdfFileContent(
            content=whole_file_summary,
            content_type=ProcessedPdfFileContentType.VISUAL_SUMMARY,
            open_ai_file_id=upload_file_to_open_ai(file_content),
        )
    )

    pages = split_pdf_into_pages(file_content=file_content)
    print(f"PDF whole summary: {whole_file_summary}")
    for index, page_content in enumerate(pages):
        print(f"Processing page {index + 1}")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            futures.append(
                executor.submit(
                    process_visual_summary,
                    page_content,
                    index,
                    assistant.id,
                    SUMMARIZE_PDF_PROMPT
                    + " \n\n<context> This file is one page of a larger file. only reference the file that you can search for.</context>  If there is an electrical schematic, describe all connections and features of the diagram.  If there is a chart, describe the type of chart and the values it depicts.",
                )
            )
            futures.append(executor.submit(process_extracted_text, page_content, index))
            futures.append(
                executor.submit(process_extracted_tables, page_content, index)
            )

            for image in extract_images_from_pdf(page_content):
                futures.append(executor.submit(process_image, image, index))

            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if isinstance(result, list):
                    processed_contents.extend(result)
                elif result is not None:
                    processed_contents.append(result)
    print(processed_contents)
    return processed_contents


def pdf_page_to_image(file_content: io.BytesIO) -> list[BytesIO]:
    pdf_document = fitz.open(stream=file_content, filetype="pdf")
    images = []

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        max_size = 1500
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.ANTIALIAS)

        img_bytes_io = io.BytesIO()
        img.save(img_bytes_io, format="JPEG")
        img_bytes_io.seek(0)
        img_bytes_io.name = (
            f"{os.path.splitext(file_content.name)[0]}_page_{page_num + 1}.jpg"
        )
        images.append(img_bytes_io)

    return images


def split_pdf_into_pages(file_content: io.BytesIO) -> any:
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


def extract_text_from_pdf(file_content: io.BytesIO) -> str:
    pdf_document = fitz.open(stream=file_content, filetype="pdf")

    all_text = ""
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        all_text += page.get_text()

    return all_text


def extract_images_from_pdf(file_content: io.BytesIO) -> list[any]:
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


def extract_tables_from_pdf(file_content: io.BytesIO) -> list[any]:
    # TODO: Tabula requires a JVM
    import tabula

    tables = tabula.read_pdf(file_content, pages="all", multiple_tables=True)
    if tables:
        return tables
    else:
        return []
