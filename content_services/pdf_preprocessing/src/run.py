import asyncio
import hashlib
from utils.aws_s3 import generate_get_presigned_url
from main import preprocess, PdfInput


# this code needs to create presigned url for a pdf in s3

async def main():
    org_id = 'org_s76pU1v8LAYhTOWB'
    org_id_hash = hashlib.sha256(org_id.encode()).hexdigest()[:63]

    codebase_id = '95b897f7-3910-497a-8ca3-59882d1c0e3f'
    relative_path = 'documents/cn0556.pdf'

    object_key = f"{codebase_id}/{relative_path}"
    presigned_url = generate_get_presigned_url(key=object_key, bucket=org_id_hash)
    print(presigned_url)
    output = await preprocess(PdfInput(
        presigned_url=presigned_url,
        pdf_name=None,
        source_content_id='4f6e2a72-3f69-47ff-b967-b43733cb158e'
    ))
    print(output)


if __name__ == "__main__":
    asyncio.run(main())
