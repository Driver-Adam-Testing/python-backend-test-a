import base64
import concurrent.futures
import io
import os
import time
from io import BytesIO

import fitz
import modal
from openai import OpenAI
from PIL import Image
from pydantic import BaseModel

from shared.agent.agent_openai_strict import OpenAIStrictAgent
from shared.agent.models.openai.file_search import query_file
from shared.interfaces.agents.data_scope import DataScope
from shared.interfaces.file_content.pdf_file_content import (
    ProcessedPdfFileContent,
    ProcessedPdfFileContentType,
)
from shared.utils.openai_file import upload_file_to_open_ai

client = OpenAI()

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

If you cannot access any file information, return 'I cannot access the file'.
"""


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
    model="gpt-4o-mini",
    tools=[{"type": "file_search"}],
)


class SummaryValidation(BaseModel):
    """
    is_valid_summary_of_file is true if the text is a summary of a file.
    is_valid_summary_of_file is false if the text alerts the user that information is missing or could not be accessed.
    """

    is_valid_summary_of_a_file: bool


def validate_summary(summary: str) -> bool:
    agent = OpenAIStrictAgent(
        model="gpt-4o-mini",
        response_format=SummaryValidation,
        scope=DataScope(organization_id="no-org", node_ids=[], user_id="pdf-inspector"),
        log=False,
    )
    response: SummaryValidation = agent.invoke(
        f"Return a ValidateSummary object based on the text: {summary}"
    )
    return response.is_valid_summary_of_a_file


def summarize_pdf_with_retry(
    file_content: io.BytesIO, summarization_query: str, assistant_id: str
) -> str | None:
    attempts = 3
    file_id = upload_file_to_open_ai(file_content)
    for attempt in range(attempts):
        try:
            whole_file_summary = query_file(
                file_id=file_id, query=summarization_query, assistant_id=assistant_id
            )

            if validate_summary(whole_file_summary):
                return whole_file_summary
            else:
                raise Exception("Could not validate summary")

        except Exception as e:
            if attempt < attempts - 1:
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in 30 seconds...")
                time.sleep(30)
            else:
                print(f"All {attempts} attempts failed: {e}")


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
            print(f"Unsupported image type: {file_extension}")
            continue

        encoded_images.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{image_media_type};base64,{image_data}"},
            }
        )

    encoded_images.append(
        {
            "type": "text",
            "text": prompt if prompt is not None else DESCRIBE_IMAGE_PROMPT,
        }
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": encoded_images,
            }
        ],
        max_tokens=1024,
    )
    return response.choices[0].message.content


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
        print(f"Processing page {index + 1}")
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
    try:
        whole_file_summary = summarize_pdf_with_retry(
            file_content, SUMMARIZE_PDF_PROMPT, assistant.id
        )
    except Exception as e:
        whole_file_summary = None
        send_exception_email = modal.Function.lookup(
            "pdf-summary-embedding", "send_exception_email"
        )
        exception_type = type(e).__name__
        exc_tb = e.__traceback__
        filename = exc_tb.tb_frame.f_code.co_filename
        line_number = exc_tb.tb_lineno
        exception_details = (
            f"Exception type: {exception_type}\nFile: {filename}\nLine: {line_number}"
        )
        print(exception_details)
        send_exception_email.spawn(exception_details)

    if whole_file_summary is None:
        pages = split_pdf_into_pages(file_content=file_content)
        pdf_page_images = extract_images_from_pdf(file_content)[:7]
        image_summary = summarize_images(pdf_page_images, prompt=DESCRIBE_IMAGE_PROMPT)
        processed_contents.append(
            ProcessedPdfFileContent(
                content=image_summary,
                content_type=ProcessedPdfFileContentType.EXTRACTED_IMAGE_SUMMARY,
            )
        )
    else:
        processed_contents.append(
            ProcessedPdfFileContent(
                content=whole_file_summary,
                content_type=ProcessedPdfFileContentType.VISUAL_SUMMARY,
            )
        )

    pages = split_pdf_into_pages(file_content=file_content)
    print(f"PDF whole summary: {whole_file_summary}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=150) as executor:
        futures = []
        for index, page_content in enumerate(pages):
            try:
                pdf_page_image = pdf_page_to_image(page_content)[0]
                futures.append(executor.submit(process_image, pdf_page_image, index))
            except Exception as e:
                print(
                    f"WARNING: An error occurred while converting PDF page to image on page {index + 1}: {e}"
                )
            futures.append(executor.submit(process_extracted_text, page_content, index))
            # TODO: move this to outer loop to process multi-page tables.
            futures.append(
                executor.submit(process_extracted_tables, page_content, index)
            )

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

        max_size = 2048
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.LANCZOS)

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


def extract_images_from_pdf(file_content: io.BytesIO) -> list[BytesIO]:
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

    try:
        tables = tabula.read_pdf(file_content, pages="all", multiple_tables=True)
    except Exception:
        return []
    if tables:
        return tables
    else:
        return []
