import sys

import modal

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python pdf_modal_test.py <content_id>")
        sys.exit(1)

    content_id = sys.argv[1]
    stub = modal.Function.lookup("pdf-inspector-test", "create_and_embed_pdf_summaries")
    stub.remote(content_id)
