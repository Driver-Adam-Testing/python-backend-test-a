import io
import os

from openai import OpenAI


def upload_file_to_open_ai(file_content: io.BytesIO):
    if os.environ.get("AZURE_OPENAI_BASE_URL"):
        base_url = os.environ["AZURE_OPENAI_BASE_URL"]
        base_url = f"https://{base_url}/openai/v1/"
        api_key = os.environ["AZURE_OPENAI_KEY_1"]
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
    else:
        client = OpenAI()
    file = client.files.create(file=file_content, purpose="assistants")
    return file.id
