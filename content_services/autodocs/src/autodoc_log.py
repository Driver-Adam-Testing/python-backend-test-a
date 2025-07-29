import json
import os
from dataclasses import dataclass

import modal
from common import app


@dataclass
class AutoDocLog:
    # NOTE: The fields in this class are implicitly linked to the schema of the following Notion database.
    #
    # https://www.notion.so/driverai/AutoDoc-Usage-Logging-22e8f239606f808ba292f4fae43a94b7
    #
    # Any changes must be synced manually.

    title: str
    user_email: str
    organization_id: str
    sources: str
    toml_content: str
    autodoc_content: str
    user_context: str
    env: str
    page_id: str
    config_kind: str

    _NOTION_DATABASE_ID = "22e8f239606f80e0898cd9cdfb1a46f5"

    def _split_into_rich_text_array(self, content: str) -> list:
        MAX_NOTION_BLOCK_UPDATE_LENGTH = 2000
        return [
            {"text": {"content": content[i : i + MAX_NOTION_BLOCK_UPDATE_LENGTH]}}
            for i in range(0, len(content), MAX_NOTION_BLOCK_UPDATE_LENGTH)
        ]

    def to_dict(self) -> dict:
        return {
            "parent": {"database_id": self._NOTION_DATABASE_ID},
            "properties": {
                "Title": {"title": [{"text": {"content": self.title}}]},
                "User Email": {"email": self.user_email},
                "Organization ID": {
                    "rich_text": [
                        {
                            "text": {"content": self.organization_id},
                            "annotations": {"code": True},
                        }
                    ]
                },
                "Sources": {
                    "rich_text": self._split_into_rich_text_array(self.sources)
                },
                "User Context": {
                    "rich_text": self._split_into_rich_text_array(self.user_context)
                },
                "Environment": {
                    "rich_text": [
                        {
                            "text": {"content": self.env},
                            "annotations": {"code": True},
                        }
                    ]
                },
                "Page ID": {
                    "rich_text": [
                        {
                            "text": {"content": self.page_id},
                            "annotations": {"code": True},
                        }
                    ]
                },
                "Config Kind": {
                    "rich_text": [
                        {
                            "text": {"content": self.config_kind},
                            "annotations": {"code": True},
                        }
                    ]
                },
            },
            "children": [
                {
                    "object": "block",
                    "type": "code",
                    "code": {
                        "caption": [],
                        "rich_text": self._split_into_rich_text_array(
                            self.toml_content
                        ),
                        "language": "toml",
                    },
                },
                {
                    "object": "block",
                    "type": "code",
                    "code": {
                        "caption": [],
                        "rich_text": self._split_into_rich_text_array(
                            self.autodoc_content
                        ),
                        "language": "markdown",
                    },
                },
            ],
        }


@app.function(
    image=modal.Image.debian_slim(python_version="3.12")
    .pip_install(["notion-client"])
    .add_local_python_source("common", copy=True),
    secrets=[
        modal.Secret.from_name("notion_write_only_api_key"),
    ],
)
def write_autodoc_log(log: AutoDocLog) -> None:
    from notion_client import Client

    notion_api_key = os.environ["NOTION_WRITE_ONLY_API_KEY"]
    notion = Client(auth=notion_api_key)
    payload = log.to_dict()
    notion.pages.create(**payload)
    print(
        "AutoDoc log written with the following payload:\n",
        json.dumps(payload, indent=2),
    )
