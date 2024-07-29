import asyncio
import os
from pathlib import Path

import boto3
import modal
from database.models_v1 import (
    Chunk,
    Codebase,
    ContentMetadata,
    ContentType,
    DerivedContent,
)
from sqlmodel import select

db_sem = asyncio.Semaphore(5)
modal_sem = asyncio.Semaphore(200)

app = modal.App("embedding")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .copy_local_dir("../../driver_db/", remote_path="/driver_db")
    .copy_local_dir(local_path="../../packages/shared", remote_path="/packages/shared")
    .poetry_install_from_file("pyproject.toml")
)


@app.function(
    image=image,
    mounts=[
        modal.Mount.from_local_dir(
            local_path="../../driver_db/certs",
            remote_path="/root/data/",
        )
    ],
    secrets=[modal.Secret.from_name("open-ai")],
    timeout=60 * 60,
    concurrency_limit=5,
)
async def generate_embeddings_for_source_contents(
    file_content: str, long_description: str, symbols_dcs: list, relative_path: str
) -> dict:
    from shared.embedding.embed_helpers import (
        generate_embeddings_for_string,
    )

    ret_dict = {}
    if file_content is not None:
        try:
            fc_splits, fc_embeds = await generate_embeddings_for_string(file_content)
            ret_dict["file_content"] = {
                "success": True,
                "splits": fc_splits,
                "embeds": fc_embeds,
            }
        except Exception as e:
            print(f"Error embedding file content on {relative_path}: {e}")
            ret_dict["file_content"] = {"success": False, "splits": [], "embeds": []}
    else:
        ret_dict["file_content"] = {"success": False, "splits": [], "embeds": []}

    if long_description is not None:
        try:
            ld_splits, ld_embeds = await generate_embeddings_for_string(
                long_description
            )
            ret_dict["long_description"] = {
                "success": True,
                "splits": ld_splits,
                "embeds": ld_embeds,
            }
        except Exception as e:
            print(f"Error embedding long description on {relative_path}: {e}")
            ret_dict["long_description"] = {
                "success": False,
                "splits": [],
                "embeds": [],
            }
    else:
        ret_dict["long_description"] = {"success": False, "splits": [], "embeds": []}

    ret_dict["symbols"] = {}
    if symbols_dcs is not None:
        for sym in symbols_dcs:
            if sym.misc_metadata.get("description") is not None:
                try:
                    s_splits, s_embeds = await generate_embeddings_for_string(
                        sym.misc_metadata["description"]
                    )
                    ret_dict["symbols"][
                        sym.misc_metadata["name"] + ":" + str(sym.misc_metadata["line"])
                    ] = {"success": True, "splits": s_splits, "embeds": s_embeds}
                except Exception as e:
                    print(
                        f"Error embedding symbol {sym.misc_metadata['name']} on {relative_path}: {e}"
                    )
                    ret_dict["symbols"][
                        sym.misc_metadata["name"] + str(sym.misc_metadata["line"])
                    ] = {"success": False, "splits": [], "embeds": []}

    return ret_dict


async def persist_embeddings(
    session,
    split_documents: list,
    embeds: list,
    content_type: ContentType,
    codebase_id: str,
    workspace_id: str,
    relative_path: str,
    metadata: dict | None = None,
) -> bool:
    from sqlmodel import delete, select

    if metadata is None:
        metadata = {}
    if len(split_documents) > 0:
        try:
            cm_res = await session.exec(
                select(ContentMetadata)
                .where(ContentMetadata.codebase_id == codebase_id)
                .where(ContentMetadata.relative_path == relative_path)
                .where(ContentMetadata.content_type == content_type)
                .where(ContentMetadata.workspace_id == workspace_id)
            )
            cm = cm_res.first()
            if cm is not None:
                # Delete existing chunks associated with cm
                print("existing metadata: ", cm.relative_path, cm.content_type)
                await session.exec(
                    delete(Chunk).where(Chunk.content_metadata_id == cm.id)
                )
                cm.misc_metadata = metadata
            else:
                cm = ContentMetadata(
                    workspace_id=workspace_id,
                    misc_metadata=metadata,
                    content_type=content_type,
                    relative_path=relative_path,
                    codebase_id=codebase_id,
                )
                print("creating: ", relative_path, content_type)

            session.add(cm)
            line_number = 0
            if content_type == ContentType.CODE_SYMBOL and "line" in metadata:
                line_number = metadata["line"]
            [
                session.add(
                    Chunk(
                        text_embedding_3_small=e,
                        text=d.text,
                        content_metadata_id=cm.id,
                        chunk_number=i,
                        token_count=len(d.tokens),
                        line_number=line_number if line_number != 0 else d.start_line,
                    )
                )
                for i, (d, e) in enumerate(zip(split_documents, embeds, strict=False))
            ]
            return True
        except Exception as e:
            print(f"Error embedding {relative_path}: {e}")
            return False
    else:
        return True


@app.function(
    image=image,
    mounts=[
        modal.Mount.from_local_dir(
            local_path="../../driver_db/certs",
            remote_path="/root/data/",
        ),
    ],
    secrets=[modal.Secret.from_name("aws-inspector-s3"), modal.Secret.from_name("db")],
    proxy=modal.Proxy.from_name("pg-proxy"),
    timeout=60 * 60 * 5,
    concurrency_limit=2,
    region="us-east",
)
async def embed_content_for_codebase(codebase_id: str, workspace_id: str) -> None:
    from database.db import async_engine
    from sqlmodel.ext.asyncio.session import AsyncSession

    # Get all source content IDs for the codebase
    async with AsyncSession(async_engine) as session:
        async with session.begin():
            sc_res = await session.exec(
                select(DerivedContent.id)
                .where(DerivedContent.codebase_id == codebase_id)
                .where(DerivedContent.source_content_id == None)  # noqa
            )
            source_content_ids = sc_res.all()

    embed_results = await asyncio.gather(
        *[
            embed_content_for_source_content(
                source_content_id, codebase_id, workspace_id
            )
            for source_content_id in source_content_ids
        ]
    )

    failed_ids = []
    for res in embed_results:
        if res["success"] is False:
            failed_ids.append(res["source_content_id"])
    if len(failed_ids) > 0:
        print(f"Failed to embed the following ids: {failed_ids}")


async def embed_content_for_source_content(
    source_content_id: str, codebase_id: str, workspace_id: str
) -> dict:
    from database.db import async_engine
    from shared.embedding.embed_helpers import (
        download_source_content_file,
        get_derived_content_type_uuid,
        get_source_content_type_uuid,
    )
    from sqlmodel.ext.asyncio.session import AsyncSession

    is_analyzable = False
    long_description = None
    file_content = None
    symbols_dcs = None

    try:
        # Get all content to embed
        async with db_sem:
            async with AsyncSession(async_engine) as session:
                async with session.begin():
                    cb_res = await session.exec(
                        select(Codebase).where(Codebase.id == codebase_id)
                    )
                    codebase = cb_res.first()
                    sc = (
                        await session.exec(
                            select(DerivedContent).where(
                                DerivedContent.id == source_content_id
                            )
                        )
                    ).first()

                    # TODO: what about older versions of the content without analysis_metadata?
                    if sc.misc_metadata is not None:
                        is_analyzable = sc.misc_metadata.get("is_analyzable")
                    else:
                        is_analyzable = False

                    file_sc_type_id = await get_source_content_type_uuid(
                        "codebase-file", session
                    )
                    dir_sc_type_id = await get_source_content_type_uuid(
                        "codebase-directory", session
                    )
                    cb_sc_type_id = await get_source_content_type_uuid(
                        "codebase", session
                    )
                    sc_type_id = sc.content_type_id

                    if is_analyzable or sc_type_id in [dir_sc_type_id, cb_sc_type_id]:
                        ld_dc_type_id = await get_derived_content_type_uuid(
                            "long_description", session
                        )
                        dc = (
                            await session.exec(
                                select(DerivedContent)
                                .where(
                                    DerivedContent.source_content_id
                                    == source_content_id
                                )
                                .where(DerivedContent.content_type_id == ld_dc_type_id)
                            )
                        ).first()

                        # Only embedding things with derived content
                        if dc is not None:
                            long_description = dc.content
                            # Make the long description from chunks if available
                            cd_dc_type_id = await get_derived_content_type_uuid(
                                "chunk_descriptions", session
                            )

                            chunks = (
                                await session.exec(
                                    select(DerivedContent)
                                    .where(
                                        DerivedContent.source_content_id
                                        == source_content_id
                                    )
                                    .where(
                                        DerivedContent.content_type_id == cd_dc_type_id
                                    )
                                )
                            ).all()

                            if len(chunks) > 1:
                                long_description = " ".join([c.content for c in chunks])

                            if (
                                sc_type_id == file_sc_type_id
                            ):  # analyzable file w/ derived content
                                # Symbols
                                symbols_dc_type_id = (
                                    await get_derived_content_type_uuid(
                                        "symbol", session
                                    )
                                )
                                symbols_dcs = (
                                    await session.exec(
                                        select(DerivedContent)
                                        .where(
                                            DerivedContent.source_content_id
                                            == source_content_id
                                        )
                                        .where(
                                            DerivedContent.content_type_id
                                            == symbols_dc_type_id
                                        )
                                    )
                                ).all()
                    session.expunge_all()

        # Download the source file
        if (
            is_analyzable
            and long_description is not None
            and sc_type_id == file_sc_type_id
        ):
            s3_client = boto3.client(
                "s3", endpoint_url=os.environ.get("AWS_S3_ENDPOINT_URL")
            )
            download_abs_path = download_source_content_file(
                s3_client=s3_client,
                codebase_storage_url=codebase.storage_url,
                codebase_root=codebase.resource_root,
                source_content_rel_path=sc.relative_path,
                download_root=Path("codebase"),
            )
            with open(download_abs_path) as r_file:
                file_content = r_file.read()

        async with modal_sem:
            embed_dict = await generate_embeddings_for_source_contents.remote.aio(
                file_content=file_content,
                long_description=long_description,
                symbols_dcs=symbols_dcs,
                relative_path=sc.relative_path,
            )

        async with db_sem:
            async with AsyncSession(async_engine) as session:
                async with session.begin():
                    if embed_dict["file_content"]["success"]:
                        await persist_embeddings(
                            session=session,
                            split_documents=embed_dict["file_content"]["splits"],
                            embeds=embed_dict["file_content"]["embeds"],
                            content_type=ContentType.SOURCE_CODE,
                            codebase_id=codebase_id,
                            workspace_id=workspace_id,
                            relative_path=sc.relative_path,
                        )
                    if embed_dict["long_description"]["success"]:
                        await persist_embeddings(
                            session=session,
                            split_documents=embed_dict["long_description"]["splits"],
                            embeds=embed_dict["long_description"]["embeds"],
                            content_type=ContentType.FILE_SUMMARY,
                            codebase_id=codebase_id,
                            workspace_id=workspace_id,
                            relative_path=sc.relative_path,
                        )
                    if symbols_dcs is not None:
                        for sym in symbols_dcs:
                            if sym.misc_metadata.get("description") is not None:
                                symbol_embed_dict = embed_dict["symbols"][
                                    sym.misc_metadata["name"]
                                    + ":"
                                    + str(sym.misc_metadata["line"])
                                ]
                                if symbol_embed_dict["success"]:
                                    sym_rel_path = (
                                        sc.relative_path
                                        + ":"
                                        + sym.misc_metadata["name"]
                                        + ":"
                                        + str(sym.misc_metadata["line"])
                                    )
                                    await persist_embeddings(
                                        session=session,
                                        split_documents=symbol_embed_dict["splits"],
                                        embeds=symbol_embed_dict["embeds"],
                                        content_type=ContentType.CODE_SYMBOL,
                                        codebase_id=codebase_id,
                                        workspace_id=workspace_id,
                                        relative_path=sym_rel_path,
                                        metadata=sym.misc_metadata,
                                    )
        return {"source_content_id": source_content_id, "success": True}
    except Exception as e:
        print(
            f"Error embedding content for Source Content ID: {source_content_id}: {e}"
        )
        return {"source_content_id": source_content_id, "success": False}


@app.local_entrypoint()
def main():
    embed_content_for_codebase.remote(
        "2838d5a4-b5ed-4117-9104-f10d2276113d", "5ae5c437-5697-4063-9136-0a5ba9394be0"
    )
