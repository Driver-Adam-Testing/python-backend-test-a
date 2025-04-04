import concurrent.futures
import os

import modal

app = modal.App("pdf-summary-embedding")

image_jve = (
    modal.Image.debian_slim(python_version="3.12")
    .copy_local_dir("../../driver_db/", remote_path="/driver_db")
    .copy_local_dir(local_path="../../packages/shared", remote_path="/packages/shared")
    .poetry_install_from_file("pyproject.toml")
    .apt_install("default-jre")
)

pdf_preprocessing_modal_config = {
    "image": image_jve,
    "mounts": [
        modal.Mount.from_local_dir(
            local_path="../../driver_db/certs",
            remote_path="/root/data/",
        ),
    ],
    "secrets": [
        modal.Secret.from_name("driver-api-credentials"),
        modal.Secret.from_name("open-ai"),
        modal.Secret.from_name("db"),
        modal.Secret.from_name("aws-inspector-s3"),
        modal.Secret.from_name("anthropic"),
    ],
    "proxy": modal.Proxy.from_name("pg-proxy")
    if os.environ["MODAL_ENVIRONMENT"] != "staging"
    else None,
    "concurrency_limit": 20,
}


@app.function(
    image=modal.Image.debian_slim(python_version="3.12").pip_install("sendgrid"),
    secrets=[
        modal.Secret.from_name("sendgrid"),
        modal.Secret.from_name("env-name"),
    ],
)
def send_exception_email(exception_details: str) -> None:
    import sendgrid
    from sendgrid.helpers.mail import Content, Email, Mail, To

    env_name = os.environ.get("ENV_NAME")
    sendgrid_api_key = os.environ.get("SENDGRID_API_KEY")

    sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)
    from_email = Email("support@driverai.com")  # Replace with your email
    to_email = To("support@driverai.com")  # Replace with recipient's email
    subject = f"MODAL {env_name}: Exception Occurred"
    content = Content("text/plain", f"An exception occurred: {exception_details}")
    mail = Mail(from_email, to_email, subject, content)

    try:
        response = sg.send(mail)
        print(f"Email sent: {response.status_code}")
    except Exception as e:
        print(f"Error sending email: {e}")


@app.function(timeout=16200, **pdf_preprocessing_modal_config, cpu=32.0)
def create_and_embed_pdf_summaries(node_id: str) -> None:
    import io

    import requests
    from database.db import engine
    from database.models_v1 import ChunkAndEmbedding, DerivedContent
    from database.models_v2 import Node, Version
    from database.models_v2_enums import ContentKind, VersionStatus
    from shared.chunking.text_splitter import split_text
    from shared.embedding.text_embedder import batch_embed_text
    from shared.file_storage.s3 import (
        get_presigned_url,
    )
    from shared.interfaces.file_content.pdf_file_content import ProcessedPdfFileContent
    from shared.pipelines.process_file.process_file_pdf import run_process_pdf
    from sqlalchemy.orm import selectinload
    from sqlmodel import Session, select

    print(f"Processing {node_id!s}")
    try:
        # TODO: call an orm function to do this.
        with Session(engine) as session:
            node = session.exec(
                select(Node)
                .where(Node.id == node_id)
                .options(selectinload(Node.version).selectinload(Version.primary_asset))
            ).one()

            presigned_url = get_presigned_url(
                organization_id=node.version.primary_asset.organization_id,
                path=f"{node.version.primary_asset_id}/{node.version_id}/{node.relative_path}",
            )

        response = requests.get(presigned_url)
        print(str(presigned_url))
        response.raise_for_status()

        pdf_content = io.BytesIO(response.content)
        pdf_content.name = node.relative_path.split("/")[-1]
        results = run_process_pdf(pdf_content)
        futures = {}
        results_splits_embeds = []
        print("Embedding pdf content...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            for result in results:
                # Remove NUL characters from the content
                cleaned_content = str(result.content.replace("\x00", ""))
                splits = split_text(cleaned_content)
                if not splits:
                    results_splits_embeds.append((result, None, None))
                else:
                    futures[executor.submit(batch_embed_text, splits)] = [
                        result,
                        splits,
                    ]
            for future in concurrent.futures.as_completed(futures):
                result, splits = futures[future]
                try:
                    embeds = future.result()
                except Exception as e:
                    print("Could not embed: ")
                    print(str(splits))
                    raise e
                results_splits_embeds.append((result, splits, embeds))

        print("persisting to database...")

        def persist_to_db(
            result: ProcessedPdfFileContent, splits: list, embeds: list
        ) -> None:
            with Session(engine) as session:
                content_kind = result.content_type.value

                if content_kind not in ContentKind:
                    # TODO: run_process_pdf uses ProcessedPdfFileContentType enum from shared/interfaces
                    # but we have the num in driver_db for content_kind, we should use that instead.
                    raise Exception(
                        f"Matching ContentKind not found for value: {result.content_type.value}"
                    )

                # TODO: This should all be in a service.

                # Remove NUL characters from the content
                cleaned_content = str(result.content.replace("\x00", ""))

                derived_content = DerivedContent(
                    content_kind=content_kind,
                    node_id=node_id,
                    relative_path=node.relative_path,
                    content=cleaned_content,
                    misc_metadata={
                        "open_ai_file_id": result.open_ai_file_id,
                        "page": result.page,
                    },
                )
                session.add(derived_content)
                session.commit()
                session.refresh(derived_content)
                if embeds:
                    for i, split in enumerate(splits):
                        session.add(
                            ChunkAndEmbedding(
                                content_id=derived_content.id,
                                text=split.text,
                                chunk_number=i,
                                text_embedding_3_small=embeds[i],
                            )
                        )

                    session.commit()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            db_futures = []
            for result, splits, embeds in results_splits_embeds:
                db_futures.append(
                    executor.submit(persist_to_db, result, splits, embeds)
                )
            for future in concurrent.futures.as_completed(db_futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error persisting to db: {e}")

        # Re-query the content object and update its status
        with Session(engine) as session:
            node = session.exec(
                select(Node)
                .where(Node.id == node_id)
                .options(selectinload(Node.version))
            ).one()
            node.version.status = VersionStatus.GENERATION_COMPLETE
            session.commit()

    except Exception as e:
        exception_type = type(e).__name__
        exc_tb = e.__traceback__
        filename = exc_tb.tb_frame.f_code.co_filename
        line_number = exc_tb.tb_lineno
        exception_details = (
            f"Exception type: {exception_type}\nFile: {filename}\nLine: {line_number}"
        )
        print(exception_details)
        send_exception_email.remote(exception_details)
        raise e

    return results
