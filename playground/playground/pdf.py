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
    run_process_pdf(file_path)
    click.echo("PDF processing completed.")


if __name__ == "__main__":
    cli()
