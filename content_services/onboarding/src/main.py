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
    .copy_local_dir("../../driver_db/", remote_path="/driver_db")
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
        ),
    ],
    secrets=[modal.Secret.from_name("aws-inspector-s3"), modal.Secret.from_name("db")],
    proxy=modal.Proxy.from_name("pg-proxy")
    if os.environ["MODAL_ENVIRONMENT"] != "staging"
    else None,
    timeout=60 * 60,
    region="us-east",
    concurrency_limit=5,
)
def run_codebase_onboarding(
    presigned_url: str,
    archive_name: str,
    org_id: str,
    creator_id: str,
    workspace_id: str,
    provider: str,
) -> None:
    from database.db import engine
    from database.models_v1 import Codebase, DerivedContent, Enum_Codebase_Status
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

    print(f"Downloaded {archive_name} from S3")

    codebase_name = None
    if provider == "github":
        codebase_name = archive_name.rsplit(".", 1)[0]

    # Override so unpack from github doesn't have hash in name.
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
        s3_dest_root = Path(str(codebase_id)) / "source"

        for root, _, files in os.walk(extracted_path):
            all_directories.append(root)
            for filename in files:
                local_path = Path(root) / filename

                file_stats = run_file_stats_and_reencode(
                    local_path,
                )
                codebase_stats[local_path] = file_stats
                if not codebase_stats[local_path]["is_blacklisted"]:
                    uploaded_dest_path = upload_file_to_s3(
                        upload_bucket, s3_dest_root, local_path
                    )
                print(f"Uploaded {local_path} to {uploaded_dest_path}")

        with Session(engine) as session, session.begin():
            base_url = create_base_storage_url(org_id)
            final_storage_url = urljoin(base_url, str(codebase_id))
            codebase = Codebase(
                id=codebase_id,
                codebase_name=codebase_name,
                creator_id=creator_id,
                description="",
                resource_root=f"{extracted_path!s}/",
                storage_url=final_storage_url,
                workspace_id=workspace_id,
                status=Enum_Codebase_Status.processing,
            )
            print(codebase)
            session.add(codebase)
            # Flush here to confirm that Source Contents created after this will know that the
            # codebase exists
            session.flush()
            print(
                f"Created but not commited codebase: {extracted_path!s}, with ID: {codebase_id}"
            )

            cb_sc_uuid = get_source_content_type_uuid("codebase")
            cb_sc = DerivedContent(
                codebase_id=codebase_id,
                relative_path=str(extracted_path),
                content_type_id=cb_sc_uuid,
                workspace_id=workspace_id,
                misc_metadata={},
            )
            session.add(cb_sc)

            # Add directories source contents
            dir_sc_uuid = get_source_content_type_uuid("codebase-directory")
            for directory in all_directories:
                if not is_on_blacklist(Path(directory)):
                    # TODO: analysis metadata for directories?
                    # TODO: this is fragile - consider using DAG logic here
                    dir_sc = DerivedContent(
                        codebase_id=codebase_id,
                        relative_path=directory,
                        content_type_id=dir_sc_uuid,
                        workspace_id=workspace_id,
                        misc_metadata={},
                    )
                    session.add(dir_sc)
                    print(f"Created but not committed source content for: {directory}.")

            # Add file source contents
            for file_path in codebase_stats:
                if not codebase_stats[file_path]["is_blacklisted"]:
                    file_sc_type = get_source_content_type_uuid("codebase-file")
                    file_sc = DerivedContent(
                        codebase_id=codebase_id,
                        relative_path=str(file_path),
                        content_type_id=file_sc_type,
                        workspace_id=workspace_id,
                        misc_metadata=codebase_stats[file_path],
                    )
                    session.add(file_sc)

                    print(
                        f"Created but not commited source content for: {file_path}. Processable: {codebase_stats[file_path]['is_analyzable']}. Stats: {codebase_stats[file_path]}"
                    )

    print("Codebase onboarding complete for codebase id: ", codebase_id)
    return codebase_id


@app.function(
    image=image,
    mounts=[
        modal.Mount.from_local_python_packages("database"),
        modal.Mount.from_local_dir(
            local_path="../../driver_db/certs/",
            remote_path="/root/data/",
        ),
    ],
    secrets=[modal.Secret.from_name("aws-inspector-s3"), modal.Secret.from_name("db")],
    proxy=modal.Proxy.from_name("pg-proxy")
    if os.environ["MODAL_ENVIRONMENT"] != "staging"
    else None,
    timeout=24 * 60 * 60,
    region="us-east",
    concurrency_limit=5,
)
def onboard_and_inspect(
    presigned_url: str,
    archive_name: str,
    org_id: str,
    creator_id: str,
    workspace_id: UUID,
    provider: str = "manual",
) -> None:
    from database.db import engine
    from database.models_v1 import (
        Codebase,
        DerivedContent,
        Enum_Codebase_Status,
        Enum_Derived_Content_Status,
    )
    from sqlmodel import Session, select
    from utils import get_source_content_type_uuid

    # TODO: send email on failure at any step in this process
    print(
        f"Onboarding for: {archive_name} from {provider} with org_id: {org_id}, creator_id: {creator_id}, workspace_id: {workspace_id} with presigned_url: {presigned_url}"
    )
    try:
        inspect_db = modal.Function.lookup("inspector-v2", "inspect_db")

        codebase_id = run_codebase_onboarding.remote(
            presigned_url, archive_name, org_id, creator_id, workspace_id, provider
        )
        print("onboarding complete for codebase: ", codebase_id)

        run_id = uuid4()
        print("Inspecting...")
        print("Inspection ID: ", run_id)
        inspect_db.remote(codebase_id, run_id)
        print("Inspection complete")

        # Update codebase status to processing-complete
        with Session(engine) as session, session.begin():
            codebase = session.get(Codebase, codebase_id)
            if codebase:
                codebase.status = Enum_Codebase_Status.processing_complete
                session.add(codebase)
            else:
                raise Exception(f"Codebase with ID: {codebase_id} not found.")

            cb_sc_uuid = get_source_content_type_uuid("codebase")
            sel_statement = select(DerivedContent).where(
                DerivedContent.codebase_id == codebase_id,
                DerivedContent.content_type_id == cb_sc_uuid,
            )
            codebase_dc = session.exec(sel_statement).first()
            if codebase_dc:
                codebase_dc.status = Enum_Derived_Content_Status.generation_complete
                session.add(codebase_dc)
            else:
                raise Exception(
                    f"Codebase Source Content with ID: {codebase_id} not found."
                )
    except Exception as e:
        exception_type = type(e).__name__
        exc_tb = e.__traceback__
        filename = exc_tb.tb_frame.f_code.co_filename
        line_number = exc_tb.tb_lineno
        exception_details = (
            f"Exception type: {exception_type}\nFile: {filename}\nLine: {line_number}"
        )
        send_exception_email.remote(exception_details)
        raise e


@app.function(
    image=modal.Image.debian_slim(python_version="3.12").pip_install("sendgrid"),
    secrets=[modal.Secret.from_name("sendgrid"), modal.Secret.from_name("env-name")],
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


@app.local_entrypoint()
def main() -> None:
    presigned_url = "https://development-codebase-dropzone.s3.us-east-1.amazonaws.com/codebases/470aeda416cbd987632d5d931bff4d7923b93ea7e89ab5ed8499599adef0943/bat-test-2.zip?response-content-disposition=inline&X-Amz-Security-Token=IQoJb3JpZ2luX2VjELD%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJHMEUCIArdoBeV5ZRmec2vqLvPLEBxoHzPVYJCEBBs2WM8VC58AiEA4Jowe71KItsIApqEeTB7qbohN0oSBXVIAAWhWqyWx2Eq1wMIqf%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FARABGgw1NTAwODI3NjExMDkiDOGfksQjgFR3nQUEzCqrA0oBzNfvpczG9CXbA%2FpNuuE79vA9hDjPusl1YKr61tjRSa%2BAo%2FOyKRe53lW%2BKpEDMnp4PdLL3Rq3mBWRru5ekk2Wpo98ps7756XorL0a2%2Fk%2BLFLu1Q74isvoEP%2BfLHCk06WNVGbgae2mKHIDKHPQtiAj3KD618rvms9wlxYcY1Frp689Bp4Ae7ptbjRAxtY6F1uRGD4TEgMqwxudJI9yLMJbr3LVIspPyAzXIb%2FXPTPI6ebvtIlrgfs13wdZjNL7IwY6ddv0pGxAeb2hkxNZHvKTFfMSqSVW%2FYdFJK4C7sSSF2trlPAfV4o2g%2FsL1LrTepuz4dsugc%2BcZJNRDmWnPu36r%2BhZoSv6Salc6hkvu4Sq4cZ225EnvPTa3gAEhot88uLEW7zrhL5TOU%2Bra8CzrJugNvC5qgWB1nsd0ckg1dHAKaW%2BVkGRGdg%2B1BlhKGvYfUJvkBh0NEYPSvEgcn%2BfDdqeoje32chOcVM%2B1Q24dMgK4IKpeQTVeLPus7KURpwnmRHnb5R2s%2FkhIBybUv5DxIGjs4HiuFCXi06fDozFlQ8wj7nrgj2KExqOA2wwjPjttQY6lAJ49ExUgmbZMqqlKhG126q4AiRE7CreY%2FPS53VtTvg2QlVkwwYQ3KbPcBXNLB02hJdlp6Jv0WGaVGa6YiAh5qJWgEOhSVa6GJiCMiDbuCy%2B0VVUCMs09MbVjT6yW1%2FDxoRXFjlUCOP1O7ZR7SKormDFqP5FMiHF8tdRWVv4vJEIeVn6aWYY%2FV%2B%2FmEgOk%2Bbl3aXTVgWQvm7IvzGJ6xIhx3mizYYFZks704BdT%2BtG3eACRmAK995gR4XfZZa%2F2Nu3JFm%2BN3R0XG64S3OOt1PLttk4BSLR4nXMB%2FUX0hE18K4r%2FgxhBiol5yqhuusUx1xj9Xtb8qJ38XRNc9twt3VlXgMNuH9QkX87pu%2FkiibjvAYml72HANk%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20240813T193033Z&X-Amz-SignedHeaders=host&X-Amz-Expires=43200&X-Amz-Credential=ASIAYAE342GK7DGKERXL%2F20240813%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=c785d8fa4f2bd3459eac7997286174c6ac762891ad71bb7cb5739a4ad204b417"
    archive_name = "bat-test-2.zip"
    org_id = "470aeda416cbd987632d5d931bff4d7923b93ea7e89ab5ed8499599adef0943"
    creator_id = "auth0|6650e02b9812cd674f78cf75"
    workspace_id = UUID("7fe232eb-37ae-4820-8439-0a10dabde8b2")

    # if modal.is_local():
    #     from dotenv import load_dotenv
    #     load_dotenv()
    #     run_codebase_onboarding.local(s3_bucket_name, s3_prefix, archive_name, org_id, creator_id, workspace_id)
    # else:
    onboard_and_inspect.remote(
        presigned_url, archive_name, org_id, creator_id, workspace_id
    )
