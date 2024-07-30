import argparse
import json
import os
import time
import webbrowser

import markdown
from shared.pipelines.create_app_note import (
    CreateAppNoteRequest,
    create_app_note,
)
from shared.pipelines.run_agent import RunAgentRequest, run_agent

html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Markdown Content</title>
    <style>
        /* Add CSS styling here if needed */
        pre {{
            background-color: #f0f0f0;
            padding: 0.5em;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div id="content">
        {markdown_content}
    </div>
    <script>
        var content = document.getElementById('content');
        var text = content.innerHTML;
        text = text.replace(/`{{3}}([^`]+)`{{3}}/g, '<pre>$1</pre>');
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
        content.innerHTML = text;
    </script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Run the operation.")
    parser.add_argument(
        "--create_app_note", action="store_true", help="Run create_app_note operation"
    )
    parser.add_argument(
        "--workspace_id", "--workspace", type=str, required=True, help="Workspace ID"
    )
    parser.add_argument(
        "--codebase_id", "--codebase", type=str, required=True, help="Codebase ID"
    )
    parser.add_argument(
        "--prompt", type=str, required=True, help="Prompt for the operation"
    )
    parser.add_argument(
        "--operation",
        type=str,
        default="create_app_note",
        help="Operation to run: create_app_note, run_agent",
    )
    parser.add_argument(
        "--options",
        type=str,
        default="{}",
        help="Additional options in JSON format",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default=None,
        help="Output file to save the response",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o",
        help="Model to use for the operation",
    )

    args = parser.parse_args()
    print(args.options)
    try:
        if args.options:
            options = json.loads(args.options)
    except json.JSONDecodeError:
        raise ValueError("Invalid options: Not a valid JSON")

    start_time = time.time()

    if args.operation == "run_agent":
        run_agent_request = RunAgentRequest(
            workspace_id=args.workspace_id,
            codebase_id=args.codebase_id,
            prompt=args.prompt,
            options=options,
        )
        response = run_agent(run_agent_request)

    elif args.operation == "create_app_note":
        create_app_note_request = CreateAppNoteRequest(
            workspace_id=args.workspace_id,
            codebase_id=args.codebase_id,
            prompt=args.prompt,
            options=options,
            model=args.model,
        )
        response = create_app_note(create_app_note_request)
    else:
        raise ValueError(f"Invalid operation: {args.operation}")

    end_time = time.time()
    execution_time = end_time - start_time

    output_file = (
        args.output_file
        if args.output_file
        else f"./output/{args.operation}_{int(time.time())}.json"
    )
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        output = {
            "response": response,
            "execution_time": execution_time,
            "input_parameters": {
                "workspace_id": args.workspace_id,
                "codebase_id": args.codebase_id,
                "prompt": args.prompt,
                "operation": args.operation,
                "options": options,
                "model": args.model,
            },
        }
        json.dump(output, f, indent=4)

    # Convert markdown response to HTML and open in browser
    def format_dict_to_markdown(input_dict, parent_key=""):
        markdown_content = ""
        for key, value in input_dict.items():
            new_key = f"{parent_key}.{key}" if parent_key else key
            if isinstance(value, dict):
                markdown_content += format_dict_to_markdown(value, new_key)
            else:
                markdown_content += (
                    f"**{new_key}**: {markdown.markdown(str(value))}\n\n"
                )
        return markdown_content

    markdown_content = format_dict_to_markdown(output)
    html = html_template.format(markdown_content=markdown_content)
    path = os.path.abspath(f"/tmp/temp_{int(time.time())}.html")
    url = "file://" + path

    with open(path, "w") as f:
        f.write(html)
    webbrowser.open(url)


if __name__ == "__main__":
    main()
