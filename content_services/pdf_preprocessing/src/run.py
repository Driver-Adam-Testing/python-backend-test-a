import asyncio
import hashlib
from utils.aws_s3 import generate_get_presigned_url
from main import preprocess, PdfInput


# this code needs to create presigned url for a pdf in s3

async def main():
    org_id = 'org_s76pU1v8LAYhTOWB'
    org_id_hash = hashlib.sha256(org_id.encode()).hexdigest()[:63]

    codebase_id = '8aed1938-adca-4097-801f-ee7121fc9067'
    relative_path = 'documents/AD4114+%281%29.pdf'

    object_key = f"{codebase_id}/{relative_path}"
    presigned_url = generate_get_presigned_url(key=object_key, bucket=org_id_hash)
    print(presigned_url)
    await preprocess(PdfInput(
        presigned_url=presigned_url,
        pdf_name=None,
        source_content_id='e81caf63-95bd-4f34-b84f-0f750df1da40'
    ))


if __name__ == "__main__":
    asyncio.run(main())
