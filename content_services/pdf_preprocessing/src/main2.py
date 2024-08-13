import modal

app = modal.App("pdf-inspector-test")

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
    ],
    "proxy": modal.Proxy.from_name("pg-proxy"),
    "concurrency_limit": 5,
    "region": "us-east",
}


@app.function(timeout=3600, **pdf_preprocessing_modal_config)
def process_pdf(pdf_url: str, source_content_id: str) -> None:
    import io

    import requests
    from shared.pipelines.process_file.process_file_pdf import run_process_pdf

    # Fetch the PDF from the URL
    response = requests.get(pdf_url)
    response.raise_for_status()  # Ensure we notice bad responses

    # Convert the content to a BytesIO object
    pdf_content = io.BytesIO(response.content)
    pdf_content.name = pdf_url.split("/")[-1]  # Set a name for the BytesIO object

    # Process the PDF content
    results = run_process_pdf(pdf_content)

    for result in results:
        print("here's where I'd save the content")

        print(result)

    return results
