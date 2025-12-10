import os
import subprocess
import tempfile

current_file_path = os.path.abspath(__file__)
puppeteer_config_path = os.path.join(
    os.path.dirname(current_file_path), "puppeteer-config.json"
)

print(f"Current file absolute path: {current_file_path}")
print(f"Puppeteer config absolute path: {puppeteer_config_path}")


def is_mermaid_renderable(mermaid_code: str) -> tuple:
    """
    Checks if a given Mermaid code block can be rendered by the Mermaid CLI.

    :param mermaid_code: The Mermaid diagram source as a string
    :return: A tuple (True, None) if renderable, (False, error_message) otherwise
    """
    # Create a temporary file for the Mermaid code
    with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as tmp_file:
        tmp_file.write(mermaid_code)
        tmp_file.flush()
        mermaid_filepath = tmp_file.name

    # We don't actually need the output file, but we must give mmdc an output path.
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as output_file:
        output_path = output_file.name

    try:
        print(f"Puppeteer config absolute path: {puppeteer_config_path}")
        print(f"Mermaid filepath: {mermaid_filepath}")
        print(f"Output path: {output_path}")
        print(f"Puppeteer config absolute path: {puppeteer_config_path}")
        print(f"Mermaid code: {mermaid_code}")
        # Try rendering. If mmdc cannot parse the file, it will raise CalledProcessError.
        subprocess.check_output(
            [
                "mmdc",
                "--puppeteerConfigFile",
                puppeteer_config_path,
                "-i",
                mermaid_filepath,
                "-o",
                output_path,
            ],
            stderr=subprocess.STDOUT,
        )
        # If successful, the code is valid
        return True, None

    except subprocess.CalledProcessError as e:
        # In case the command fails, capture the output for debugging
        error_message = e.output.decode("utf-8", errors="ignore")
        print("Mermaid CLI error:", error_message)
        return False, error_message

    finally:
        # Clean up: remove temporary files
        if os.path.exists(mermaid_filepath):
            os.remove(mermaid_filepath)
        if os.path.exists(output_path):
            os.remove(output_path)
