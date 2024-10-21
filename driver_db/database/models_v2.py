import enum
import uuid
from datetime import UTC, datetime
from typing import Optional, Union
from uuid import UUID

from pgvector.sqlalchemy import Vector
from pydantic import BaseModel, field_validator, model_validator
from sqlalchemy import (
    Column,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as SaUuid
from sqlmodel import Field, Relationship, SQLModel

from .config import settings
from .custom_types import TSVector


# DEMO -> Node Types
class NodeTypeEnum(str, enum.Enum):
    FOLDER = "FOLDER"
    FILE = "FILE"
    PAGE = "PAGE"


# DEMO -> Node objects
class Node(SQLModel, table=True):
    """
    Represents a Node entity in the database, which can be a folder, file, or page within an organization.

    Attributes:
        id (UUID): Unique identifier for the node, automatically generated.
        path (str): The unique path of the node, used to determine its location and type.
        custom_display_name (str): Optional custom name for display purposes.
        organization_id (str): Identifier for the organization to which the node belongs.
        created_at (datetime): Timestamp of when the node was created, defaults to the current UTC time.
        updated_at (datetime): Timestamp of the last update to the node, automatically updated.

    Relationships:
        contents (List[Content]): List of content items associated with the node.
        tags (List[Tag]): List of tags associated with the node, through a secondary relationship.
        children (List[Node]): List of child nodes, representing a hierarchical structure.
        parent (Optional[Node]): The parent node, if any, in the hierarchical structure.

    Properties:
        node_type (str): Derived property indicating the type of node (FOLDER, FILE, or PAGE) based on its path.
        absolute_path (str): Derived property providing the full path including the organization ID.
        display_name (str): Derived property for the display name, using custom_display_name if available.
        source_url (str): Derived property providing an S3 URL using a hash of the organization_id.
        application_url (str): Derived property providing a URL using the app_id from config and the URL-encoded path.

    Methods:
        is_child(parent_node_or_path: Node | str) -> bool:
            Determines if the current node is a child of the given parent node or path.

        is_parent(child_node_or_path: Node | str) -> bool:
            Determines if the current node is a parent of the given child node or path.
    """

    __tablename__ = "nodes"
    __table_args__ = (
        UniqueConstraint("organization_id", "path", name="uq_organization_id_path"),
    )

    id: UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(
            SaUuid(as_uuid=True),
            primary_key=True,
            server_default=text("uuid_generate_v4()"),
        ),
    )
    path: str = Field(sa_column=Column(Text, nullable=False, index=True))
    custom_display_name: str = Field(
        sa_column=Column(Text, nullable=True),
    )
    organization_id: str = Field(sa_column=Column(Text, nullable=False, index=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    )

    # Relationships
    contents: list["Content"] = Relationship(
        back_populates="node",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    tags: list["Tag"] = Relationship(
        back_populates="nodes",
        sa_relationship_kwargs={"secondary": "node_tags"},
    )

    # DEMO -> children and parent can be loaded using sqlalchemy. Then we can build already authorized, topographical joins in python.
    children: list["Node"] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={
            "primaryjoin": "and_(Node.organization_id == foreign(Node.organization_id), Node.path.like(foreign(Node.path) + '/%'))",
            "cascade": "all, delete-orphan",
        },
    )
    parent: Optional["Node"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={
            "primaryjoin": "and_(Node.organization_id == remote(Node.organization_id), Node.path.like(remote(Node.path) + '/%'))",
            "order_by": "func.length(Node.path).desc()",
            "uselist": False,
        },
    )
    ancestors: list["Node"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "and_(Node.organization_id == remote(Node.organization_id), Node.path.like(remote(Node.path) + '/%'))",
            "order_by": "func.length(Node.path).desc()",
        },
    )

    # Derived Properties

    # DEMO -> Node type is derived. The .driver_page is an example of how we could encode that information into the path.
    @property
    def node_type(self) -> str:
        if self.path.endswith(".driver_page") and "/" in self.path:
            return NodeTypeEnum.PAGE.value
        elif self.path.endswith("/"):
            return NodeTypeEnum.FOLDER.value
        else:
            return NodeTypeEnum.FILE.value

    # DEMO -> absolute paths as a model attribute. We can create absolute paths that are always available.
    @property
    def absolute_path(self) -> str:
        return f"{self.organization_id}/{self.path}"

    @absolute_path.setter
    def absolute_path(self, value: str) -> None:
        try:
            organization_id, path = value.split("/", 1)
            self.organization_id = organization_id
            self.path = path
        except ValueError:
            raise ValueError(
                "Invalid absolute path format. Expected format: 'organization_id/path'"
            )

    # DEMO -> Display name property
    @property
    def display_name(self) -> str:
        if self.custom_display_name:
            return self.custom_display_name
        elif self.node_type == NodeTypeEnum.FOLDER.value:
            return self.path.rstrip("/").split("/")[-1]
        else:
            return self.path.split("/")[-1]

    @display_name.setter
    def display_name(self, value: str) -> None:
        self.custom_display_name = value

    # DEMO -> Source URL property !!!! Needs to work right, I don't think it does. Must check with Eric
    @property
    def source_url(self) -> str:
        import hashlib

        hash_object = str(hashlib.sha256(self.organization_id.encode()))[:63]
        hash_hex = hash_object.hexdigest()
        return f"https://s3.amazonaws.com/{hash_hex}/{self.path}"

    # DEMO -> Application URL property --- This is an interesting one because it needs to conform via convention with the urls on the frontend.
    @property
    def application_url(self) -> str:
        from urllib.parse import quote

        encoded_path = quote(self.path)
        return f"{settings.APPLICATION_HOST}/{encoded_path}"

    # Methods
    # DEMO -> Our child checks can be on here. There may be a way to overload relationships so that it can traverse the path to get direct children.
    def is_child(self, parent_node_or_path: Union["Node", str]) -> bool:
        if isinstance(parent_node_or_path, Node):
            return self.absolute_path.startswith(
                parent_node_or_path.absolute_path.rstrip("/") + "/"
            )
        elif isinstance(parent_node_or_path, str):
            return self.path.startswith(
                parent_node_or_path.rstrip("/") + "/"
            ) or self.absolute_path.startswith(parent_node_or_path.rstrip("/") + "/")

    def is_parent(self, child_node_or_path: Union["Node", str]) -> bool:
        if isinstance(child_node_or_path, Node):
            return child_node_or_path.absolute_path.startswith(
                self.absolute_path.rstrip("/") + "/"
            )
        elif isinstance(child_node_or_path, str):
            return child_node_or_path.startswith(
                (self.path.rstrip("/") + "/", self.absolute_path.rstrip("/") + "/")
            )


# DEMO: NodeDto for API interactions
class NodeDto(BaseModel):
    id: UUID | None
    path: str
    created_at: datetime | None
    updated_at: datetime | None
    node_type: str
    display_name: str | None
    organization_id: str | None
    parent_node: Optional["NodeDto"] = None
    child_nodes: list["NodeDto"] | None = None

    @classmethod
    def from_node(cls, node: Node) -> "NodeDto":
        return cls(
            id=node.id,
            path=node.path,
            created_at=node.created_at,
            updated_at=node.updated_at,
            node_type=node.node_type,
            display_name=node.display_name,
            organization_id=node.organization_id,
            parent_node=cls.from_node(node.parent_node) if node.parent_node else None,
            child_nodes=[cls.from_node(child) for child in node.child_nodes]
            if node.child_nodes
            else None,
        )

    def to_node(self) -> Node:
        kwargs = {"path": self.path}
        if self.id is not None:
            kwargs["id"] = self.id
        if self.display_name is not None:
            kwargs["custom_display_name"] = self.display_name
        if self.organization_id is not None:
            kwargs["organization_id"] = self.organization_id
        if self.created_at is not None:
            kwargs["created_at"] = self.created_at
        if self.updated_at is not None:
            kwargs["updated_at"] = self.updated_at
        node = Node(**kwargs)

        return node


# DEMO -> Content Categories
class ContentCategoryEnum(str, enum.Enum):
    SOURCE_TEXT = "SOURCE_TEXT"  # DEMO -> This signifies a sanitized extraction directly from source. These cannot be mutated
    USER_GENERATED = "USER_GENERATED"  # DEMO -> These should not be Embedded because they can be constantly mutated
    SYSTEM_GENERATED = "SYSTEM_GENERATED"  # DEMO -> These are usually IRs


# DEMO -> These are client filter terms. They should not be used to determine logical path for post-processing.
class ContentTypeEnum(str, enum.Enum):
    LONG_SUMMARY = "LONG_SUMMARY"
    SHORT_SUMMARY = "SHORT_SUMMARY"
    SYMBOL_DEFINITION = "SYMBOL_DEFINITION"
    PDF_TEXT = "PDF_TEXT"
    PDF_IMAGE = "PDF_IMAGE"
    USER_NOTE_TEXT = "USER_NOTE_TEXT"
    TEMPLATE_CODE = "TEMPLATE_CODE"


class Content(SQLModel, table=True):
    __tablename__ = "contents"

    id: UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(
            SaUuid(as_uuid=True),
            primary_key=True,
        ),
    )
    node_id: UUID = Field(
        sa_column=Column(
            SaUuid(as_uuid=True), ForeignKey("nodes.id"), nullable=False, index=True
        ),
    )
    content_type: str = Field(
        sa_column=Column(Text, nullable=False),
    )
    category: str = Field(
        sa_column=Column(Text, nullable=False),
    )
    content: str | None = Field(sa_column=Column(Text, nullable=True))
    content_metadata: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    )

    # Relationships
    node: Node = Relationship(
        back_populates="contents",
    )
    chunks: list["Chunk"] = Relationship(
        back_populates="content",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    # Validators
    @field_validator("content_type")
    def validate_content_type(cls, value: str) -> str:
        if value not in ContentTypeEnum.__members__:
            raise ValueError(f"Invalid content_type: {value}")
        return value

    @field_validator("category")
    def validate_category(cls, value: str) -> str:
        if value not in ContentCategoryEnum.__members__:
            raise ValueError(f"Invalid category: {value}")
        return value

    @model_validator(mode="before")
    def check_immutable_source_text(cls, values: dict) -> dict:
        if (
            values.get("id")
            and values.get("category") == ContentCategoryEnum.SOURCE_TEXT.value
        ):
            raise ValueError(
                "Cannot modify a Content record with category SOURCE_TEXT once it is created."
            )
        return values


class Chunk(SQLModel, table=True):
    __tablename__ = "chunks"

    id: UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(
            SaUuid(as_uuid=True),
            primary_key=True,
        ),
    )
    content_id: UUID = Field(
        sa_column=Column(
            SaUuid(as_uuid=True), ForeignKey("contents.id"), nullable=False, index=True
        ),
    )
    text: str = Field(sa_column=Column(Text, nullable=False))
    text_embedding_3_small: list[float] = Field(
        sa_column=Column(
            Vector(1536), nullable=True
        )  # TODO this column will need to be indexed ONCE POPULATED1
    )
    chunk_number: int = Field(sa_column=Column(Integer, nullable=False))
    chunk_metadata: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )

    # Relationships
    content: Content = Relationship(
        back_populates="chunks",
    )
    __ts_vector__: any = Column(
        "__ts_vector__",
        TSVector(),
        Computed("to_tsvector('english', text)", persisted=True),
    )
    __table_args__ = (
        Index(
            "ix_chunkandembedding___ts_vector__", __ts_vector__, postgresql_using="gin"
        ),
    )


class Tag(SQLModel, table=True):
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("name", "organization_id", name="unique_tag_name_per_org_id"),
    )

    id: UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(
            SaUuid(as_uuid=True),
            primary_key=True,
        ),
    )
    name: str = Field(
        sa_column=Column(Text, nullable=False),
    )
    hex_color: str = Field(
        sa_column=Column(Text, nullable=False),
    )
    organization_id: UUID = Field(
        sa_column=Column(SaUuid(as_uuid=True), nullable=False, index=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    )

    # Relationships
    nodes: list[Node] = Relationship(
        back_populates="tags",
        sa_relationship_kwargs={"secondary": "node_tags"},
    )


class NodeTag(SQLModel, table=True):
    __tablename__ = "node_tags"

    node_id: UUID = Field(
        sa_column=Column(
            SaUuid(as_uuid=True), ForeignKey("nodes.id"), primary_key=True
        ),
    )
    tag_id: UUID = Field(
        sa_column=Column(SaUuid(as_uuid=True), ForeignKey("tags.id"), primary_key=True),
    )

    # Relationships
    node: Node = Relationship(
        back_populates="tags",
    )
    tag: Tag = Relationship(
        back_populates="nodes",
    )
