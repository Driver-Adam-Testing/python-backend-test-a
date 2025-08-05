import os
from uuid import UUID

import modal

image = (
    modal.Image.debian_slim(python_version="3.12")
    .add_local_dir(local_path="../../driver_db", remote_path="/driver_db", copy=True)
    .add_local_dir(
        local_path="../../packages/shared", remote_path="/shared_pkg", copy=True
    )
    .pip_install(
        [
            "pydantic>=2.8.2",
            "sqlmodel",
            "/shared_pkg",
            "sqlalchemy",
            "toml",
            "aiolimiter",
            "openai",
            "tiktoken",
        ]
    )
    .add_local_python_source(
        "auto_toml", "chat_openai", "logger", "prompts", "database", "shared", copy=True
    )
)

app = modal.App("auto_toml")


@app.cls(
    image=image,
    secrets=[
        modal.Secret.from_name("db"),
        modal.Secret.from_name("open-ai"),
    ],
    proxy=modal.Proxy.from_name("my-proxy")
    if os.environ["MODAL_ENVIRONMENT"] in ["dev", "staging"]
    else modal.Proxy.from_name("my-proxy", environment_name="prod"),
    memory="2048",
    timeout=3600 * 8,
    region="us-east",
    retries=0,
)
class AutoTomlModal:
    @modal.method()
    async def generate_from_page_id(
        self,
        page_id: str,
        enable_auto_scaling: bool,
        document_goal: str,
        user_context: str = "",
    ) -> str:
        from auto_toml import AutoToml

        auto_toml = AutoToml.from_page_id(
            page_id=UUID(page_id), enable_auto_scaling=enable_auto_scaling
        )
        return await auto_toml.generate(
            document_goal=document_goal, user_context=user_context
        )

    @modal.method()
    async def generate_from_node_ids(
        self,
        node_ids: list[str],
        enable_auto_scaling: bool,
        document_goal: str,
        user_context: str = "",
    ) -> str:
        from auto_toml import AutoToml

        auto_toml = AutoToml.from_node_ids(
            node_ids=node_ids, enable_auto_scaling=enable_auto_scaling
        )
        return await auto_toml.generate(
            document_goal=document_goal, user_context=user_context
        )

    @modal.method()
    async def append_from_page_id(
        self,
        page_id: str,
        enable_auto_scaling: bool,
        user_toml: str,
        user_context: str = "",
    ) -> str:
        from auto_toml import AutoToml

        auto_toml = AutoToml.from_page_id(
            page_id=UUID(page_id), enable_auto_scaling=enable_auto_scaling
        )
        return await auto_toml.append(user_toml=user_toml, user_context=user_context)

    @modal.method()
    async def append_from_node_ids(
        self,
        node_ids: list[str],
        enable_auto_scaling: bool,
        user_toml: str,
        user_context: str = "",
    ) -> str:
        from auto_toml import AutoToml

        auto_toml = AutoToml.from_node_ids(
            node_ids=node_ids, enable_auto_scaling=enable_auto_scaling
        )
        return await auto_toml.append(user_toml=user_toml, user_context=user_context)


@app.local_entrypoint()
async def main(page_id: str, document_goal: str) -> None:
    auto_toml_modal = AutoTomlModal()
    auto_toml_modal.generate_from_page_id.remote(
        page_id=page_id, enable_auto_scaling=True, document_goal=document_goal
    )
