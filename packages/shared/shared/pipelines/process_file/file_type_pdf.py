import io
import os

import fitz  # PyMuPDF
from openai import OpenAI


# TODO: this is presuming that I have a file. perhaps it's better to operate on a byte array only? Not use disk?
def run_process_pdf(file_content: io.BytesIO, file_name: str):
    file_id = upload_file_to_open_ai(
        file_content, file_name=os.path.basename(file_name)
    )
    print(f"Uploaded file ID: {file_id}")

    whole_file_summary = summarize_file(file_id=file_id)
    print(whole_file_summary)

    pages = split_pdf_into_individual_pages(file_name)

    for page in pages:
        with open(page, "rb") as f:
            page_content = f.read()

        page_file_id = upload_file_to_open_ai(
            page_content, file_name=os.path.basename(page)
        )
        # print(f"Uploaded page ID: {page_file_id}")

        # Summarize each page
        page_summary = summarize_file(file_id=page_file_id, context=whole_file_summary)
        print(page_summary)

        page_text = extract_text_from_pdf(page)
        print(page_text)

        page_tables = extract_tables_from_pdf(page)
        print(page_tables)

        page_images = extract_images_from_pdf(page)
        for image in page_images:
            with open(image, "rb") as img_file:
                image_content = img_file.read()

            # Upload each image to OpenAI
            image_file_id = upload_file_to_open_ai(
                image_content, file_name=os.path.basename(image)
            )
            print(f"Uploaded image ID: {image_file_id}")

            image_summary = summarize_file(file_id=image_file_id)
            print(image_summary)


def split_pdf_into_individual_pages(file_name):
    def save_page_as_pdf(pdf_document, page_num, output_dir):
        page = pdf_document.load_page(page_num)
        print(page)
        single_page_pdf = fitz.open()
        single_page_pdf.insert_pdf(pdf_document, from_page=page_num, to_page=page_num)
        output_path = os.path.join(
            output_dir, f"{os.path.splitext(file_name)[0]}_page_{page_num + 1}.pdf"
        )
        single_page_pdf.save(output_path)
        print(f"Saved page {page_num + 1} to {output_path}")
        return output_path

    try:
        pdf_document = fitz.open(file_name)
        print(f"Successfully opened PDF: {file_name}")

        # Create a directory to store individual page PDFs
        output_dir = f"{os.path.splitext(file_name)[0]}_pages"
        os.makedirs(output_dir, exist_ok=True)

        created_files = []

        # Split PDF into individual pages
        for page_num in range(len(pdf_document)):
            output_path = save_page_as_pdf(pdf_document, page_num, output_dir)
            created_files.append(output_path)

        return created_files
    except Exception as e:
        print(f"Error processing PDF {file_name}: {e}")
        return None


def extract_text_from_pdf(file_name):
    try:
        pdf_document = fitz.open(file_name)
        print(f"Successfully opened PDF: {file_name}")

        all_text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            all_text += page.get_text()

        return all_text
    except Exception as e:
        print(f"Error extracting text from PDF {file_name}: {e}")
        return None


def extract_images_from_pdf(file_name):
    try:
        pdf_document = fitz.open(file_name)
        print(f"Successfully opened PDF: {file_name}")

        images = []
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                image_filename = f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}"
                images.append((image_filename, image_bytes))
                print(f"Extracted image {image_filename} from page {page_num + 1}")

        return images
    except Exception as e:
        print(f"Error extracting images from PDF {file_name}: {e}")
        return None


def upload_file_to_open_ai(file_content, file_name):
    client = OpenAI()
    try:
        file = io.BytesIO(file_content)
        file.name = file_name
        message_file = client.files.create(file=file, purpose="assistants")
        return message_file.id
    except Exception as e:
        print(f"Error uploading PDF to vector store: {e}")
        return None


def summarize_file(file_id, context=None):
    query = "Summarize the uploaded file. Be verbose and descriptive. Describe diagrams, schematics, images, text, and tables in detail."
    if context:
        query += f" <context>This file is part of a larger context, described here: {context} </context> {query}"
    try:
        client = OpenAI()
        assistant = client.beta.assistants.create(
            name="PDF Summarizer",
            instructions="You are a microprocessors and hardware expert and technical writer.",
            model="gpt-4o",
            tools=[{"type": "file_search"}],
        )

        # Create a thread and attach the file to the message
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

        # Create a run and check the output
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            instructions="You're an expert technical writer who can understand documents.",
            assistant_id=assistant.id,
        )

        if run.status == "completed":
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            summary = messages.data[0].content[0].text.value
            print(f"Summary for PDF: {summary}")
            return summary
    except Exception as e:
        print(f"Error summarizing PDF: {e}")
        return None


def extract_tables_from_pdf(file_path):
    try:
        # TODO: Tabula requires a JDK to run. Make sure the os has this.
        import tabula

        tables = tabula.read_pdf(file_path, pages="all", multiple_tables=True)
        if tables:
            print(f"Extracted {len(tables)} tables from PDF {file_path}")
            return tables
        else:
            print(f"No tables found in PDF {file_path}")
            return None
    except Exception as e:
        print(f"Error extracting tables from PDF {file_path}: {e}")
        return None
