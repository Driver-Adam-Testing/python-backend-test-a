import concurrent.futures
import hashlib
import os

from boto3 import resource
from botocore.client import ClientError
from database.models_v1 import DerivedContent
from database.models_v2 import (
    Node,
    PrimaryAsset,
    Version,
)
from database.models_v2_enums import NodeKind, PrimaryAssetKind
from sqlalchemy import create_engine
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

database_url = os.getenv("SOURCE_DATABASE_URL")
engine = create_engine(database_url)


def update_s3_keys(primary_asset_id: str, version_id: str, codebase_id: str) -> None:
    with Session(engine) as session:
        nodes_stmt = (
            select(Node)
            .where(Node.version_id == version_id, Node.kind == NodeKind.CODEBASE_FILE)
            .options(selectinload(Node.version).selectinload(Version.primary_asset))
        )
        nodes = session.exec(nodes_stmt).all()
    if len(nodes) == 0:
        print(
            f"No nodes found for primary_asset_id: {primary_asset_id}, version_id: {version_id}"
        )
        return primary_asset_id, version_id, 0, 0

    s3 = resource(
        "s3",
        aws_access_key_id=os.getenv("SRC_AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("SRC_AWS_SECRET_ACCESS_KEY"),
        region_name=os.environ['AWS_REGION'],
    )
    organization_id = nodes[0].version.primary_asset.organization_id
    hashed_org_id = hashlib.sha256(organization_id.encode()).hexdigest()[:63]
    try:
        s3.meta.client.head_bucket(Bucket=hashed_org_id)
    except ClientError:
        print(
            f"Bucket {hashed_org_id} does not exist. Skipping update for primary_asset_id: {primary_asset_id}, version_id: {version_id}"
        )
        return primary_asset_id, version_id, 0, 0

    bucket = s3.Bucket(hashed_org_id)

    pre_version_prefix_primary_asset = f"{primary_asset_id}/source/"
    post_version_prefix_primary_asset = (
        f"{primary_asset_id}/version/{version_id}/source/"
    )
    if codebase_id is not None:
        pre_version_prefix_codebase = f"{codebase_id}/source/"
        post_version_prefix_codebase = f"{codebase_id}/version/{version_id}/source/"
    else:
        pre_version_prefix_codebase = None
        post_version_prefix_codebase = None

    finalized_prefix = None
    new_prefix = f"{primary_asset_id}/{version_id}/"

    if len(list(bucket.objects.filter(Prefix=new_prefix))) > 0:
        print(f"New key already exists: {new_prefix}, taking no action")
        return primary_asset_id, version_id, len(nodes), 0
    if (
        post_version_prefix_codebase is not None
        and primary_asset_id != codebase_id
        and len(list(bucket.objects.filter(Prefix=post_version_prefix_codebase))) > 0
    ):
        # Check this one first - since we squashed multiple codebases under a single primary asset, if this matches, we take this.
        # We check the /version/ prefix first, since that will have been updated more recently as well
        print(
            f"Codebase matches post-versioning style with codebase id {post_version_prefix_codebase}, moving to new key: {primary_asset_id}/{version_id}"
        )
        finalized_prefix = post_version_prefix_codebase
    elif (
        pre_version_prefix_codebase is not None
        and primary_asset_id != codebase_id
        and len(list(bucket.objects.filter(Prefix=pre_version_prefix_codebase))) > 0
    ):
        # Same logic for checking this next, since we squashed multiple codebases under a single primary asset, if this matches, we take this,
        # but only if there is no post-versioning style match
        print(
            f"Codebase matches pre-versioning style with codebase id {pre_version_prefix_codebase}, moving to new key: {primary_asset_id}/{version_id}"
        )
        finalized_prefix = pre_version_prefix_codebase
    elif len(list(bucket.objects.filter(Prefix=post_version_prefix_primary_asset))) > 0:
        # if the primary asset is the same as the codebase, we check here first. /version/ first since it'll be more recently updated
        print(
            f"PrimaryAsset matches post-versioning style {post_version_prefix_primary_asset}, moving to new key: {primary_asset_id}/{version_id}"
        )
        finalized_prefix = post_version_prefix_primary_asset
    elif len(list(bucket.objects.filter(Prefix=pre_version_prefix_primary_asset))) > 0:
        print(
            f"PrimaryAsset matches pre-versioning style {pre_version_prefix_primary_asset}, moving to new key: {primary_asset_id}/{version_id}"
        )
        finalized_prefix = pre_version_prefix_primary_asset
    else:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(
            f"******* No known case found for primary_asset_id: {primary_asset_id}, version_id: {version_id}. Code may be missing from S3 **********"
        )
        print("!!!!!!!!!!!!!!!!!!!!!!!!!")
        return primary_asset_id, version_id, 0, len(nodes)

    edge_case_count = 0
    existing_keys = 0
    for node in nodes:
        destination_key = f"{new_prefix}{node.relative_path}"
        source_key = f"{finalized_prefix}{node.relative_path}"

        if len(list(bucket.objects.filter(Prefix=destination_key))) > 0:
            # this check just adds even more time, but good to check?
            # actually shouldn't hit this given the early return above, but could support in the future if we have a partial transfer
            print(f"New key already exists: {destination_key}, taking no action")
            existing_keys += 1
        elif len(list(bucket.objects.filter(Prefix=source_key))) > 0:
            bucket.copy({"Bucket": hashed_org_id, "Key": source_key}, destination_key)
        else:
            # On a dry run through, I did not hit this case, which is promising!
            edge_case_count += 1
            print("!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(
                f"No matching source key found for node {node.id}, {node.relative_path} in S3: {source_key}"
            )
            print("!!!!!!!!!!!!!!!!!!!!!!!!!")

    print(
        f"Updated {len(nodes) - edge_case_count - existing_keys} / {len(nodes)} keys for primary_asset_id: {primary_asset_id}, version_id: {version_id}"
    )
    if existing_keys > 0:
        print(f"Found {existing_keys} existing keys")
    if edge_case_count > 0:
        print(f"Found {edge_case_count} edge cases")
    return primary_asset_id, version_id, len(nodes), edge_case_count


with Session(engine) as session:
    primary_assets_stmt = select(PrimaryAsset).where(
        PrimaryAsset.kind == PrimaryAssetKind.CODEBASE
    )
    primary_assets = session.exec(primary_assets_stmt).all()

print(f"Found: {len(primary_assets)} primary assets of kind CODEBASE")
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = []
    for primary_asset in primary_assets:
        primary_asset_id = primary_asset.id

        with Session(engine) as session:
            versions_stmt = select(Version).where(
                Version.primary_asset_id == primary_asset.id
            )
            versions = session.exec(versions_stmt).all()

        print(
            f"Found {len(versions)} versions for primary asset {primary_asset.display_name}, {primary_asset_id}"
        )
        for version in versions:
            with Session(engine) as session:
                derived_contents_stmt = select(DerivedContent).where(
                    DerivedContent.version_id == version.id,
                    DerivedContent.content_kind == "codebase",
                )
                derived_content = session.exec(derived_contents_stmt).first()
                codebase_id = (
                    derived_content.codebase_id if derived_content is not None else None
                )

            version_id = version.id
            futures.append(
                executor.submit(
                    update_s3_keys, primary_asset_id, version_id, codebase_id
                )
            )
            # update_s3_keys(primary_asset_id, version_id, codebase_id)
    for future in concurrent.futures.as_completed(futures):
        res = future.result()
        print(
            f"Finished updating {res[2]} keys for primary_asset_id: {res[0]}, version_id: {res[1]}, with {res[3]} edge cases"
        )
