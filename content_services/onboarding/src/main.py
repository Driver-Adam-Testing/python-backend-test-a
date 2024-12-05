import json
import os
from contextlib import suppress
from datetime import datetime
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
    .copy_local_dir(local_path="../../packages/shared", remote_path="/packages/shared")
    .poetry_install_from_file("pyproject.toml")
)


@app.function(
    image=image,
    mounts=[
        modal.Mount.from_local_python_packages("utils"),
    ],
    secrets=[modal.Secret.from_name("aws-inspector-s3")],
    timeout=60 * 60,
    region="us-east",
    concurrency_limit=5,
    keep_warm=1,
)
def run_pre_codebase_analysis(
    presigned_url: str,
) -> str:
    from utils import (
        download_file_from_presigned_url,
        run_file_stats_and_reencode,
        unpack_archive,
    )

    temp_archive_name = "temp.zip"
    download_dest = Path(temp_archive_name)
    download_file_from_presigned_url(presigned_url, download_dest)

    print(f"Downloaded {temp_archive_name} from S3")

    # Override so unpack from github doesn't have hash in name.
    extracted_path = unpack_archive(download_dest)
    codebase_name = str(extracted_path)
    print("Codebase name : ", codebase_name)
    print("Unpacked archive to: ", extracted_path)

    codebase_stats = {
        "analyzable_bytes": 0,
        "analyzable_files": 0,
        "total_bytes": 0,
        "total_files": 0,
        "analyzable_files_by_extension": {},
        "analyzable_bytes_by_extension": {},
    }
    for root, _, files in os.walk(extracted_path):
        for filename in files:
            local_path = Path(root) / filename
            print(f"Analyzing {local_path}")
            file_stats = run_file_stats_and_reencode(local_path)

            if file_stats["is_analyzable"] and not file_stats["is_blacklisted"]:
                codebase_stats["analyzable_bytes"] += file_stats["size"]
                codebase_stats["analyzable_files"] += 1
                if (
                    file_stats["extension"]
                    not in codebase_stats["analyzable_files_by_extension"]
                ):
                    codebase_stats["analyzable_files_by_extension"][
                        file_stats["extension"]
                    ] = 0
                if (
                    file_stats["extension"]
                    not in codebase_stats["analyzable_bytes_by_extension"]
                ):
                    codebase_stats["analyzable_bytes_by_extension"][
                        file_stats["extension"]
                    ] = 0
                codebase_stats["analyzable_files_by_extension"][
                    file_stats["extension"]
                ] += 1
                codebase_stats["analyzable_bytes_by_extension"][
                    file_stats["extension"]
                ] += file_stats["size"]
                codebase_stats["total_bytes"] += file_stats["size"]
                codebase_stats["total_files"] += 1
            else:
                codebase_stats["total_bytes"] += file_stats["size"]
                codebase_stats["total_files"] += 1

    return json.dumps(codebase_stats)


@app.function(
    image=image,
    mounts=[
        modal.Mount.from_local_python_packages("utils"),
        modal.Mount.from_local_python_packages("database"),
        modal.Mount.from_local_python_packages("shared"),
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
    override_codebase_name: str | None = None,
) -> None:
    from database.db import engine
    from database.models_v1 import (
        Codebase,
        DerivedContent,
        Enum_Codebase_Status,
        Enum_Derived_Content_Status,
        UsageEventType,
    )
    from shared.interfaces.usage.event_metadata import (
        UsageEventMetadata,
        UsageMetric,
        UsageSessionMetadata,
    )
    from shared.usage.llm_session import LLMUsageSession
    from sqlmodel import Session
    from utils import (
        create_base_storage_url,
        create_bucket_if_dne,
        download_file_from_presigned_url,
        get_org_id_from_workspace,
        get_source_content_type_uuid,
        is_on_blacklist,
        run_file_stats_and_reencode,
        unpack_archive,
        upload_file_to_s3,
    )

    download_dest = Path(archive_name)
    download_file_from_presigned_url(presigned_url, download_dest)

    print(f"Downloaded {archive_name} from S3")

    if provider == "github":
        override_codebase_name = archive_name.rsplit(".", 1)[0]

    # Override so unpack from github doesn't have hash in name.
    extracted_path = unpack_archive(
        download_dest, override_codebase_name=override_codebase_name
    )
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
        base_url = create_base_storage_url(org_id)
        final_storage_url = urljoin(base_url, str(codebase_id))

        with Session(engine) as session, session.begin():
            print(
                f"Creating codebase and content record for codebase: {extracted_path!s} with ID: {codebase_id}"
            )
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
            session.add(codebase)

            cb_sc_uuid = get_source_content_type_uuid("codebase")
            cb_sc = DerivedContent(
                codebase_id=codebase_id,
                relative_path=str(extracted_path),
                content_type_id=cb_sc_uuid,
                workspace_id=workspace_id,
                misc_metadata={},
                status=Enum_Derived_Content_Status.generating,
            )
            session.add(cb_sc)

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
            codebase_sloc = 0
            codebase_size_in_bytes = 0
            # Add file source contents
            for file_path in codebase_stats:
                if not codebase_stats[file_path]["is_blacklisted"]:
                    file_sc_type = get_source_content_type_uuid("codebase-file")
                    misc_metadata = codebase_stats[file_path]

                    file_sc = DerivedContent(
                        codebase_id=codebase_id,
                        relative_path=str(file_path),
                        content_type_id=file_sc_type,
                        workspace_id=workspace_id,
                        misc_metadata=misc_metadata,
                    )
                    session.add(file_sc)
                    # Only add to SLOC and size if the file is analyzable
                    if codebase_stats[file_path]["is_analyzable"]:
                        codebase_sloc += misc_metadata["sloc"]
                        codebase_size_in_bytes += misc_metadata["size"]
                    print(
                        f"Created but not commited source content for: {file_path}. Processable: {codebase_stats[file_path]['is_analyzable']}. Stats: {codebase_stats[file_path]}"
                    )

        session_meta = UsageSessionMetadata(
            content_type="codebase", content_id=str(codebase_id)
        )
        # need to get the real org id from the workspace since the org_id passed in is the hashed org_id
        real_org_id = get_org_id_from_workspace(workspace_id)
        with LLMUsageSession(real_org_id, creator_id, session_meta) as llm_session:
            usage_metric = UsageMetric(
                session_id=llm_session.session_id,
                organization_id=real_org_id,
                user_id=creator_id,
                event_source="codebase_onboarding",
                bytes_in=-codebase_size_in_bytes,
                bytes_out=0,
                tokens_in=0,
                tokens_out=0,
                timestamp=datetime.now(),
                event_type=UsageEventType.ONBOARDING_USAGE_DEBIT,
                event_metadata=UsageEventMetadata(
                    model="None",
                    provider="None",
                    input={},
                    output="",
                    sloc=codebase_sloc,
                ),
            )
            llm_session.send_event(usage_metric)
            # TODO: check usage balance guardrails here

    print("Codebase onboarding complete for codebase id: ", codebase_id)
    return codebase_id


@app.function(
    image=image,
    mounts=[
        modal.Mount.from_local_python_packages("database"),
        modal.Mount.from_local_python_packages("shared"),
        modal.Mount.from_local_python_packages("utils"),
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
    # TODO: Keep-warm speeds up onboarding; let's keep till we create the codebase in the backend directly.
    # This makes the codebase show up just a bit quicker in the UI.
    keep_warm=1,
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

    def set_codebase_status(
        codebase_id: UUID, status: Enum_Derived_Content_Status
    ) -> None:
        # TODO This function is nested to skirt import issues in modal.
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
                codebase_dc.status = status
                session.add(codebase_dc)
            else:
                raise Exception(
                    f"Codebase Source Content with ID: {codebase_id} not found."
                )

    # TODO: send email on failure at any step in this process
    print(
        f"Onboarding for: {archive_name} from {provider} with org_id: {org_id}, creator_id: {creator_id}, workspace_id: {workspace_id} with presigned_url: {presigned_url}"
    )
    try:
        codebase_id = run_codebase_onboarding.remote(
            presigned_url, archive_name, org_id, creator_id, workspace_id, provider
        )
        print("onboarding complete for codebase: ", codebase_id)

        inspect_db = modal.Function.lookup("inspector-v2", "inspect_db")
        run_id = uuid4()
        print("Inspecting...")
        print("Inspection ID: ", run_id)
        inspect_db.remote(codebase_id, run_id)
        print("Inspection complete")

        set_codebase_status(
            codebase_id, Enum_Derived_Content_Status.generation_complete
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

        # Since codebase could possibly be undefined in this clean up action, we don't care if it fails
        with suppress(Exception):
            set_codebase_status(
                codebase_id, Enum_Derived_Content_Status.generation_error
            )
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
    # from utils import generate_get_presigned_url

    # archive_name = "eric-project-main.zip"
    # archive_name = "upload-test.zip"
    # org_id = "6b00f9ade1094692d388c5dc385d7dccc474504aa5778cb5389f732f36ef641"
    # # org_id = "org_s76pU1v8LAYhTOWB"
    # creator_id = "auth0|6650e02b9812cd674f78cf75"
    # workspace_id = UUID("32de9990-b63d-4e8e-9567-58e2a78292ec")
    # presigned_url = generate_get_presigned_url(
    #     "development-codebase-dropzone",
    #     # "codebases/6b00f9ade1094692d388c5dc385d7dccc474504aa5778cb5389f732f36ef641/eric-project-main.zip",
    #     "codebases/6b00f9ade1094692d388c5dc385d7dccc474504aa5778cb5389f732f36ef641/upload-test.zip",
    # )
    presigned_url = "https://development-codebase-dropzone.s3.us-east-1.amazonaws.com/codebases/6b00f9ade1094692d388c5dc385d7dccc474504aa5778cb5389f732f36ef641/upload-test.zip?response-content-disposition=inline&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEGMaCXVzLWVhc3QtMSJGMEQCIHL3%2FWrwFD8kyYZy0LfbBp9v6TrXIMRWyaHIricmidN2AiAZpAx0dUIezF8CdtZzGZ9iHPH32LGzRj9vPVcYNLb5vSq1BAgbEAEaDDU1MDA4Mjc2MTEwOSIMFjaiuxB%2FzKDjJQ2%2BKpIEM%2Fhzf6W99QmrGAkb24t6az8jaMeWJ2ZvnCAqPXaVce8jQNPGk5m9iUBE4c9uIkF%2Bv0U2fCMK%2BNTj0LGlUxSLkYk27tQX7VP9pjXT2kIcIA7Ns3NDprijSlJgfr6VoEx%2FLcBvL2OTGBoBoQbM9mBWkSszKU3r7WygJbOKAKF9oifspZblvBQa7NpW7gbMm8km13FH%2FU%2F0daMFcsOX2uPWLchNSBTDHqaxHGn5%2FNl%2BS%2F77JvndPaPn3FNWmrJqvYbYILGvzHKDON9HNOkyYHLllj4eipMCGTpgC0WfSH6NnEAU2BCnee3YHm3wlIpLnjtObRS10b0rfZpTcPLVxl%2BjYBmghtnSVEYbIlaHCv9Z1F03WwEXL%2FP9sQNtyWOMq1dg9kX1c99kdc6kVuuZACbfBKWwGSG20chaazC2nytwzB3Lva77tIkIlvfOH8yUDcXzPAASo0KObIouAcXYlbWbp5YAvaCEpufQnXMRCQMFhqTDtK9bjg053DpmzvKN8y9p8Nhtq6WqFZBk%2FiGOApBMhTgTSYtvF%2BVM2isy%2FjK3oBr8xY7shj1hlrdfAWolYnzazfSPQ5w3ykIfoRkUBKxwmqCK%2FAelxUVl%2FDsc4bLbG4R3aaaTfh1apRtMzjDjYn5KwGDVrpAe1iJ8gJQQHtwTiMJ1HQcb5jErF2qKoZtbumlg9YvaqFpQ%2BUKgKWFuPwr6jvMw3NjHugY6xgIqJGIXDd3Ew%2BcXlcanBSEOupcBNZh8gp51oQQkYZNOdxj4CwMqukYTM8jwRLQZ%2B8V8FFXnwR6zIIhgQzMczfW8dWH7gVkI7d5iqG24eCJFyjhV5b3devUkBacIFDwlcR4zfrWqKUkfPpu3SeFL7m1%2FnEIjzS9EvLNRem1rTzLRLOB9u1EXZPAY7svD8CtFVi2vJyYh4VM%2BRdYJRrKIQdOI0Ddq2HY0LycWdMIjWsEn6sFp0qiZc2ih3t2ey4PL6weBTWaRtC4bxi0NCzb04fJ6aJUBd2S4%2BgfVasDafggDKd69mCHG8CIRCFXlSPiZLnVf%2BLxvPxYMnAkW0CoooBXXYY6iE959J2yG8LbRxgPRJebKjZVb8RuFDfGS9LUgKhrmdeJXvGlw0RhT6S1qtes0Cqas75WU86XY%2FQ1zRXdazjuZzJNajg%3D%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIAYAE342GK2VPWD3NN%2F20241205%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20241205T181045Z&X-Amz-Expires=1200&X-Amz-SignedHeaders=host&X-Amz-Signature=9b3abbcdd8d888d04e4b85d904d5a5a1dfe61c5b59d760c28f7deee1a8ecd8aa"

    # if modal.is_local():
    #     from dotenv import load_dotenv
    #     load_dotenv()
    #     run_codebase_onboarding.local(s3_bucket_name, s3_prefix, archive_name, org_id, creator_id, workspace_id)
    # else:
    # onboard_and_inspect.remote(
    #     presigned_url, archive_name, org_id, creator_id, workspace_id
    # )
    file_stats = run_pre_codebase_analysis.remote(presigned_url)
    print(file_stats)


@app.local_entrypoint()
def diff_flow() -> None:
    import hashlib

    # existing_codebase_id = "e82242f5-32b4-453b-9741-7cf198f4cce1"
    # run_id = "8bd74c69-421d-4a35-8c97-fa7cb4efae48"
    archive_name_new_code = (
        "desk-control-v2.zip"  # TODO is this actually used in the code?
    )
    override_codebase_name = "desk-control-v2"
    presigned_url_of_new_code = "https://development-codebase-dropzone.s3.us-east-1.amazonaws.com/codebases/470aeda416cbd987632d5d931bff4d7923b93ea7e89ab5ed8499599adef0943/desk-control-v2.zip?response-content-disposition=inline&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEIf%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJHMEUCIQCF4UGpad%2BvqbsZpUl68XUrbo61bKMzi3nRVa%2F7gfvpEQIgTzVOUsh5cC8O3Rzm6JkxnhtZk9TqgZKEHd70T95k2eoqugQI8P%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FARABGgw1NTAwODI3NjExMDkiDOWkBlsxftjg20FuqyqOBNTEpt90OAdzT9QY9ij3Ds88daNK2smgjRBVaNxtTcDE7LCQ96D%2Bmt7q9YB0a3noBeGGGtauF8QxQ1%2BJXdWZeNVUt3jGdeJmzjWIifmFwXfbpNh0C8HeBDlCZkKf8FHpjDYZBNrGStivzQf9HEjyErXQvdQ9TZfeUaZ4TyCxiavSV3zdYQcGfzHai5yXfTxkIZ4st5qwmLifdgPzju7QKIpfgPvmLSa0Ta95a7VOv5n7Hi6qmPgS0cRLpE7Fa6LTJ5osUP698Pu3nsYhh%2B%2BU2oMnlR97fsr8wvO20L7wCxOo8D5vqPCnKpfVnxdv3MwB8UTAIqYlRlePNd2cptnJF0x20c46hgeIz54GQPjbo9NqxrgK4rszzti%2BzR4%2F5tlBKsbllGqgOsY9gcgFQgHUlUpAYXfwSzuAxoNm0KT8dCCLOoqBNpg7iGkJ2a19N8Ydj%2B8O05rDPvaZ6HthBPJiFOjKi05diVIx1A0LHqieYtUJbqosRaq5gKKiqcggyPbBgLQ%2FpbltLacIcSJjGozavFTAGoUyBpKAOPrHGkAuVC35LBZCmgHTzA7ZAMGhJhuWgVGtTv3iJ%2BjikIOuA827a8O9Te1zxSziSw84BEwSVwHoolPgj1Vyt%2B2frQ1qQK3wd6hZtns5Knt6%2FNGHBtO8%2FyWeN%2B9VOCcDtwFaGeD6%2B5rpRtFz%2FlYtMjj%2FnXplmccw4%2BPuuAY6xQLEVHHeaxvXDYRpeiUHwtAc8Xe0J%2F54QyhlNe8SWw1%2FGXYFjz6V1%2FpnWNSAKNFDQzyt88QoW0NxtYkznMqE3XvHZj2O6H63%2BCQAg8sphz0NJHSOwr7iV%2FElfE7R1zptKSbG4xBRohDYDRYxgHUJDQBHJ%2FJOuqxJZcQSmzi5mo%2Bx%2B6RBwlxpcjSo4ez7A783HBAB%2FIRNIWF%2BLUyujpWiC0gY7%2B902Ost5QzZsRymJErdsKzrlg8mwI1jHi4fsZRPxkTvfrHHV9xSHNbhJ61sECYPAcgasZXOZIji7D2gj5qlhpVkykB3jQIRW2ACKdv17ZdiXDfB2yH1StfxNgrWpniNyN4%2Bbvt%2Bw7oDe%2B%2B2qLomGFxX2PpzhTYmqI4BRimXjms7PTOxXvvSp%2Fwyl4UTDN6QcHDEft149W2BfW4lPYOdtWjyzavl&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIAYAE342GK3ZLMHSPM%2F20241025%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20241025T145912Z&X-Amz-Expires=43200&X-Amz-SignedHeaders=host&X-Amz-Signature=e401928b8807990e0361215541dcb41d5dcd0b64134dd9f78d12e16c932c9de6"
    # The above is located in 470aeda416cbd987632d5d931bff4d7923b93ea7e89ab5ed8499599adef0943 of the codebase dropzone.

    org_id = "org_s76pU1v8LAYhTOWB"
    org_id = hashlib.sha256(org_id.encode()).hexdigest()[:63]
    creator_id = "auth0|667dbba790b963e36720b911"
    workspace_id = UUID("32de9990-b63d-4e8e-9567-58e2a78292ec")

    codebase_id = run_codebase_onboarding.remote(
        presigned_url_of_new_code,
        archive_name_new_code,
        org_id,
        creator_id,
        workspace_id,
        "manual",
        override_codebase_name=override_codebase_name,
    )
    print("Onboarding complete for codebase: ", codebase_id)

    # # For testing, we are going to hard code the new codebase id while we get inspector working
    # codebase_id = "8050a448-8f5d-4ef5-9667-a10c0a146c5a"
    #
    # print("Onboarding complete for codebase: ", codebase_id)
    # inspect_db = modal.Function.lookup("inspector-v2", "inspect_db")
    # inspect_db.remote(
    #     existing_codebase_id,
    #     run_id,
    #     True,
    #     None,
    #     codebase_id,
    # )
    #
    # print("Diff flow complete for codebase: ", codebase_id)

    #
