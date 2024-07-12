import asyncio
from main import preprocess


async def main():
    await preprocess(
        source_content_id='37741946-00d8-4be0-bd89-9515e17da734'
    )


if __name__ == "__main__":
    asyncio.run(main())