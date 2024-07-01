import os
from pathlib import Path
from urllib.parse import urljoin
from uuid import UUID, uuid4

import modal

app = modal.App("codebase-onboarding")

# TODO: configuration
# TODO: parallelize

image = (
    modal.Image.debian_slim(python_version="3.12")
    .copy_local_dir('../../driver_db/', remote_path='/driver_db')
    .poetry_install_from_file("pyproject.toml")
)

@app.function(
    image=image,
    mounts=[
        modal.Mount.from_local_python_packages("utils"),
        modal.Mount.from_local_python_packages("database"),
        modal.Mount.from_local_dir(
            local_path="../../driver_db/certs/",
            remote_path="/root/data/",
        )
    ],
    secrets=[
        modal.Secret.from_name("aws-inspector-s3"),
        modal.Secret.from_name("db")
    ],
    proxy=modal.Proxy.from_name("pg-proxy"),
    timeout=60*60,
    region='us-east',
    concurrency_limit=5
)
def run_codebase_onboarding(
    presigned_url: str,
    archive_name: str,
    org_id: str,
    creator_id: str,
    workspace_id: str,
    provider: str
) -> None:
    from database.db import engine
    from database.models_v1 import (
        Codebase,
        Enum_Codebase_Status,
        SourceContent,
    )
    from sqlmodel import Session
    from utils import (
        create_base_storage_url,
        create_bucket_if_dne,
        download_file_from_presigned_url,
        get_source_content_type_uuid,
        is_on_blacklist,
        run_file_stats_and_reencode,
        unpack_archive,
        upload_file_to_s3,
    )

    download_dest = Path(archive_name)
    download_file_from_presigned_url(presigned_url, download_dest)

    print(f'Downloaded {archive_name} from S3')

    codebase_name = None
    if provider == 'github':
        codebase_name = archive_name.rsplit('.', 1)[0]

    extracted_path = unpack_archive(download_dest, override_codebase_name=codebase_name)
    codebase_name = str(extracted_path)
    print("Codebase name : ", codebase_name)
    print("Unpacked archive to: ", extracted_path)

    all_directories = []
    codebase_stats = {}

    if extracted_path.exists():
        upload_bucket = org_id
        create_bucket_if_dne(upload_bucket)
        codebase_id = uuid4()

        for root, _, files in os.walk(extracted_path):
            all_directories.append(root)
            for filename in files:
                local_path = Path(root) / filename

                file_stats = run_file_stats_and_reencode(
                    local_path,
                )
                codebase_stats[local_path] = file_stats

        s3_dest_root = Path(str(codebase_id)) / "source"
        # TODO: put this in a threadpoolexecutor
        for file_path in codebase_stats.keys():
            if not codebase_stats[file_path]['is_blacklisted']:
                uploaded_dest_path = upload_file_to_s3(upload_bucket, s3_dest_root, file_path)
                print(f"Uploaded {file_path} to {uploaded_dest_path}")

        with Session(engine) as session:
            with session.begin():
                base_url = create_base_storage_url(org_id)
                final_storage_url = urljoin(base_url, str(codebase_id))
                codebase = Codebase(
                    id=codebase_id,
                    codebase_name=codebase_name,
                    creator_id=creator_id,
                    description='',
                    resource_root=f"{str(extracted_path)}/",
                    storage_url=final_storage_url,
                    workspace_id=workspace_id,
                    status=Enum_Codebase_Status.processing
                )
                print(codebase)
                session.add(codebase)
                # Flush here to confirm that Source Contents created after this will know that the
                # codebase exists
                session.flush()
                print(f"Created but not commited codebase: {str(extracted_path)}, with ID: {codebase_id}")

                cb_sc_uuid = get_source_content_type_uuid("codebase")
                cb_sc = SourceContent(
                    codebase_id=codebase_id,
                    relative_path=str(extracted_path),
                    source_content_type_id=cb_sc_uuid,
                    workspace_id=workspace_id,
                    analysis_metadata={}
                )
                session.add(cb_sc)

                # Add directories source contents
                dir_sc_uuid = get_source_content_type_uuid("codebase-directory")
                for directory in all_directories:
                    if not is_on_blacklist(Path(directory)):
                        # TODO: analysis metadata for directories?
                        # TODO: this is fragile - consider using DAG logic here
                        dir_sc = SourceContent(
                            codebase_id=codebase_id,
                            relative_path=directory,
                            source_content_type_id=dir_sc_uuid,
                            workspace_id=workspace_id,
                            analysis_metadata={}
                        )
                        session.add(dir_sc)
                        print(f"Created but not commited source content for: {directory}.")

                # Add file source contents
                for file_path in codebase_stats.keys():
                    if not codebase_stats[file_path]['is_blacklisted']:
                        file_sc_type = get_source_content_type_uuid("codebase-file")
                        file_sc = SourceContent(
                            codebase_id=codebase_id,
                            relative_path=str(file_path),
                            source_content_type_id=file_sc_type,
                            workspace_id=workspace_id,
                            analysis_metadata=codebase_stats[file_path]
                        )
                        session.add(file_sc)

                        print(f"Created but not commited source content for: {file_path}. Processable: {codebase_stats[file_path]['is_analyzable']}. Stats: {codebase_stats[file_path]}")

    print("Codebase onboarding complete for codebase id: ", codebase_id)
    return codebase_id

@app.function(
    image=image,
    mounts=[
        modal.Mount.from_local_python_packages("database"),
        modal.Mount.from_local_dir(
            local_path="../../driver_db/certs/",
            remote_path="/root/data/",
        )
    ],
    secrets=[
        modal.Secret.from_name("aws-inspector-s3"),
        modal.Secret.from_name("db")
    ],
    proxy=modal.Proxy.from_name("pg-proxy"),
    timeout=24*60*60,
    region='us-east',
    concurrency_limit=5
)
def onboard_and_inspect(presigned_url:str, archive_name: str, org_id: str, creator_id: str, workspace_id: UUID, provider: str = 'manual'):
    from database.db import engine
    from database.models_v1 import Codebase, Enum_Codebase_Status
    from sqlmodel import Session
    #TODO: send email on failure at any step in this process
    print(f"Onboarding for: {archive_name} from {provider} with org_id: {org_id}, creator_id: {creator_id}, workspace_id: {workspace_id} with presigned_url: {presigned_url}")
    try:
        inspect_db = modal.Function.lookup("inspector-v2", "inspect_db")
        create_embeddings = modal.Function.lookup("comprehender", "create_embeddings")

        codebase_id = run_codebase_onboarding.remote(presigned_url, archive_name, org_id, creator_id, workspace_id, provider)
        print("onboarding complete for codebase: ", codebase_id)

        run_id = uuid4()
        print("Inspecting...")
        print("Inspection ID: ", run_id)
        inspect_db.remote(codebase_id, run_id)
        print("Inspection complete")
        print("Creating embeddings...")

        create_embeddings.remote(str(workspace_id), str(codebase_id))
        print("Embeddings created")

        #Update codebase status to processing-complete
        with Session(engine) as session:
            with session.begin():
                codebase = session.get(Codebase, codebase_id)
                if codebase:
                    codebase.status = Enum_Codebase_Status.processing_complete
                    session.add(codebase)
                else:
                    raise Exception(f"Codebase with ID: {codebase_id} not found.")
    except Exception as e:
        exception_type = type(e).__name__
        exc_tb = e.__traceback__
        filename = exc_tb.tb_frame.f_code.co_filename
        line_number = exc_tb.tb_lineno
        exception_details = f"Exception type: {exception_type}\nFile: {filename}\nLine: {line_number}"
        send_exception_email.remote(exception_details)
        raise e


@app.function(
    image=modal.Image.debian_slim(python_version="3.12")
    .pip_install("sendgrid"),
    secrets=[
        modal.Secret.from_name("sendgrid"),
        modal.Secret.from_name("env-name")
    ]
)
def send_exception_email(exception_details):
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


@app.local_entrypoint()
def main():
    presigned_url = ""
    archive_name = "infinity-core.zip"
    org_id = '6b00f9ade1094692d388c5dc385d7dccc474504aa5778cb5389f732f36ef641'
    creator_id = 'auth0|6650e02b9812cd674f78cf75'
    workspace_id = UUID('2fb6c92d-68cb-4864-a457-8031589e3210')

    # if modal.is_local():
    #     from dotenv import load_dotenv
    #     load_dotenv()
    #     run_codebase_onboarding.local(s3_bucket_name, s3_prefix, archive_name, org_id, creator_id, workspace_id)
    # else:
    onboard_and_inspect.remote(presigned_url, archive_name, org_id, creator_id, workspace_id)
