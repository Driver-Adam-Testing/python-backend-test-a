import io

from openai import OpenAI


def upload_file_to_open_ai(
    file_content: bytes, file_name: str = "auxiliary_document.pdf"
) -> str:
    client = OpenAI()
    file_io = io.BytesIO(file_content)
    file_io.name = file_name
    uploaded_file = client.files.create(
        file=file_io,
        purpose="assistants",
    )

    return uploaded_file.id
