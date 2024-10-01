import random

from database.db import engine
from database.derived_content_types import DerivedContentTypeNames
from database.models_v1 import (
    DerivedContent,
    DerivedContentType,
    Tag,
    TagContent,
    Workspace,
)
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

tag_colors = [
    "#737373",
    "#f97316",
    "#f59e0b",
    "#eab308",
    "#22c55e",
    "#10b981",
    "#14b8a6",
    "#0ea5e9",
    "#3b82f6",
    "#6366f1",
    "#8b5cf6",
    "#a855f7",
    "#d946ef",
    "#ec4899",
    "#f43f5e",
]


def create_workspace_tags() -> None:
    with Session(engine) as session:
        try:
            print("Fetching workspaces...")
            workspaces = session.execute(select(Workspace)).all()

            for workspace in workspaces:
                # Don't tag new "Default" workspace assets that are created in the new global UX
                if workspace[0].display_name != "Default":
                    print(f"Creating tag for workspace: {workspace[0].display_name}")
                    random_color = random.choice(tag_colors)
                    workspace_tag = Tag(
                        name=workspace[0].display_name.strip(),
                        hex_color=random_color,
                        type="tag",
                        organization_id=workspace[0].organization_id,
                        created_by="SYSTEM",
                        updated_by="SYSTEM",
                    )
                    session.add(workspace_tag)

                    # Fetch all application_notes, supplemental_documents and codebases from derived_contents
                    contents = session.execute(
                        select(DerivedContent)
                        .join(DerivedContentType)
                        .where(
                            or_(
                                DerivedContentType.type_name
                                == DerivedContentTypeNames.APPLICATION_NOTE.value,
                                DerivedContentType.type_name
                                == DerivedContentTypeNames.SUPPLEMENTAL_DOCUMENT.value,
                                DerivedContentType.type_name
                                == DerivedContentTypeNames.CODEBASE.value,
                            ),
                            DerivedContent.workspace_id == workspace[0].id,
                        )
                    ).all()

                    for content in contents:
                        print(f"Adding tag to {content[0].id}")
                        content_tag_relationship = TagContent(
                            tag=workspace_tag,
                            content_id=content[0].id,
                            include=True,
                        )
                        session.add(content_tag_relationship)

            session.commit()
        except Exception as e:
            session.rollback()
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    create_workspace_tags()
