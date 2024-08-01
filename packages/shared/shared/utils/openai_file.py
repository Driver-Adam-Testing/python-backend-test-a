import io

from openai import OpenAI


def upload_file_to_open_ai(file_content: io.BytesIO):
    client = OpenAI()
    file = client.files.create(file=file_content, purpose="assistants")
    return file.id
