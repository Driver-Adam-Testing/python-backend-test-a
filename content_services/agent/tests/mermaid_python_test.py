import os
import subprocess
import tempfile


def is_mermaid_renderable(mermaid_code: str) -> bool:
    """
    Checks if a given Mermaid code block can be rendered by the Mermaid CLI.

    :param mermaid_code: The Mermaid diagram source as a string
    :return: True if renderable, False otherwise
    """
    # Create a temporary file for the Mermaid code
    with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as tmp_file:
        tmp_file.write(mermaid_code)
        tmp_file.flush()
        mermaid_filepath = tmp_file.name

    # We don't actually need the output file, but we must give mmdc an output path.
    # We'll just point it to a temporary file with a valid extension.
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as output_file:
        output_path = output_file.name

    try:
        # Try rendering. If mmdc cannot parse the file, it will raise CalledProcessError.
        subprocess.check_output(
            ["mmdc", "-i", mermaid_filepath, "-o", output_path],
            stderr=subprocess.STDOUT,
        )
        # If successful, the code is valid
        return True

    except subprocess.CalledProcessError as e:
        # In case the command fails, capture the output for debugging
        print("Mermaid CLI error:", e.output.decode("utf-8", errors="ignore"))
        return False

    finally:
        # Clean up: remove temporary files
        if os.path.exists(mermaid_filepath):
            os.remove(mermaid_filepath)
        if os.path.exists(output_path):
            os.remove(output_path)


if __name__ == "__main__":
    # Example of valid Mermaid code:
    valid_mermaid_diagram = """
    sequenceDiagram
        participant Alice
        participant Bob
        Alice->>Bob: Hello Bob, how are you?
        Bob-->>Alice: I am good thanks!
    """

    if is_mermaid_renderable(valid_mermaid_diagram):
        print("Valid Mermaid diagram is renderable!")
    else:
        print("Valid Mermaid diagram is not renderable.")

    # Example of invalid Mermaid code:
    invalid_mermaid_diagram = """
    flowchart TB
    subgraph FPGASleepTrackerSystem
        direction TB

        Sensors[Accelerometer (I2C Data)]
        AccelSampler[accel_sampler.sv]
        UART[UART Communication (uart.sv)]
        SignalProcessing[Signal Processing (biquad.sv)]
        NeuralNetworkProcessing[Neural Network (nn_pkg)]
        FIFOBuffers[FIFO Buffers (fifo_ebr)]
        DataTransfer[Data Transfer (target_to_host_fifo)]
        HostDriver[Host Communication (Rust-based driver)]

        Sensors -->|Data| AccelSampler
        AccelSampler -->|Processed Data| SignalProcessing
        SignalProcessing -->|Featurized Data| NeuralNetworkProcessing
        NeuralNetworkProcessing -->|Output| FIFOBuffers
        FIFOBuffers -->|Buffered Data| DataTransfer
        DataTransfer -->|UART| UART
        UART -->|"Data Sent"| HostDriver

    end
    """

    if is_mermaid_renderable(invalid_mermaid_diagram):
        print("Invalid Mermaid diagram is renderable!")
    else:
        print("Invalid Mermaid diagram is not renderable.")
