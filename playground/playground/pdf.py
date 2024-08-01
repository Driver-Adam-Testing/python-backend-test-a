import io
import os

import click
from shared.pipelines.process_file.file_type_pdf import run_process_pdf


@click.group()
def cli():
    """CLI for PDF operations."""
    pass


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
def process_file(file_path):
    """Process a local PDF file using the run_process_pdf function."""
    click.echo(f"Processing PDF file: {file_path}")
    with open(file_path, "rb") as f:
        file_content = io.BytesIO(f.read())
        file_content.name = os.path.basename(file_path)

    contents = run_process_pdf(file_content)
    output_dir = "pdf_processing_results"
    os.makedirs(output_dir, exist_ok=True)

    for index, content in enumerate(contents):
        output_file_path = os.path.join(
            output_dir,
            f"{os.path.splitext(os.path.basename(file_path))[0]}_content_{index + 1}.json",
        )
        with open(output_file_path, "w") as output_file:
            output_file.write(str(content.model_dump()))

    for content in contents:
        click.echo(content)
        click.prompt("Press Enter to continue...", default="", show_default=False)
    click.echo("PDF processing completed.")


if __name__ == "__main__":
    cli()
