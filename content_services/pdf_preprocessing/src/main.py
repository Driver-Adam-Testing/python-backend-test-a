import json
import os
import fitz
import requests
from openai import OpenAI
from pydantic import BaseModel
from config import settings
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from urllib.parse import urlparse

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
        model="gpt-4o",
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


def create_content_metadata(pdf_summary, page_summaries):
    content_metadata = {
        'pdf_summary': pdf_summary,
        'page_summaries': page_summaries
    }
    return content_metadata


def save_metadata(content_metadata):
    # Placeholder for saving metadata to the database
    print(content_metadata)
    return content_metadata


def embed_metadata(content_metadata):
    # Placeholder for embedding metadata
    return content_metadata


class PdfInput(BaseModel):
    presigned_url: str
    pdf_name: str | None = None


def preprocess(input: PdfInput):
    presigned_url = input.presigned_url
    pdf_name = input.pdf_name or os.path.basename(urlparse(presigned_url).path)
    download_path = f'./pdfs/{pdf_name}'

    # Download the PDF
    pdf_path = download_pdf(presigned_url, download_path)
    # pdf_path = '/Users/ghostmac/Downloads/AD7173-8.pdf'
    
    # Split PDF into pages
    pages = split_pdf_into_pages(pdf_path)

    # Summarize the PDF and its pages
    pdf_summary, page_summaries = summarize_pdf_content(pages)

    # Create content metadata
    content_metadata = create_content_metadata(pdf_summary, page_summaries)

    # Save and embed metadata
    save_metadata(content_metadata)
    content_metadata = embed_metadata(content_metadata)
    with open(f'./metadata/{pdf_name}_metadata.json', 'w') as json_file:
        json.dump(content_metadata, json_file, indent=4)
    return content_metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a PDF file.')
    parser.add_argument('presigned_url', type=str, help='The presigned URL of the PDF file.')

    args = parser.parse_args()

    output = preprocess(PdfInput(presigned_url=args.presigned_url, pdf_name=None))
    print(output)