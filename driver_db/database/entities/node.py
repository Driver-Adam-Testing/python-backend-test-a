import enum
from typing import Union

from database.models_v2 import NodeTableRow


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


# DEMO -> Node Types
class NodeTypeEnum(str, enum.Enum):
    FOLDER = "FOLDER"
    FILE = "FILE"
    PAGE = "PAGE"


class Node(NodeTableRow):
    # Derived Properties
    # DEMO -> Node type is derived. The .driver_page is an example of how we could encode that information into the path.
    # @property
    # def node_type(self) -> str:
    #     if self.path.endswith(".driver_page") and "/" in self.path:
    #         return NodeTypeEnum.PAGE.value
    #     elif self.path.endswith("/"):
    #         return NodeTypeEnum.FOLDER.value
    #     else:
    #         return NodeTypeEnum.FILE.value

    # # DEMO -> absolute paths as a model attribute. We can create absolute paths that are always available.
    # @property
    # def absolute_path(self) -> str:
    #     return f"{self.organization_id}/{self.path}"

    # @absolute_path.setter
    # def absolute_path(self, value: str) -> None:
    #     try:
    #         organization_id, path = value.split("/", 1)
    #         self.organization_id = organization_id
    #         self.path = path
    #     except ValueError:
    #         raise ValueError(
    #             "Invalid absolute path format. Expected format: 'organization_id/path'"
    #         )

    # # DEMO -> Display name property
    # @property
    # def display_name(self) -> str:
    #     if self.custom_display_name:
    #         return self.custom_display_name
    #     elif self.node_type == NodeTypeEnum.FOLDER.value:
    #         return self.path.rstrip("/").split("/")[-1]
    #     else:
    #         return self.path.split("/")[-1]

    # @display_name.setter
    # def display_name(self, value: str) -> None:
    #     self.custom_display_name = value

    # # DEMO -> Source URL property !!!! Needs to work right, I don't think it does. Must check with Eric
    # @property
    # def source_url(self) -> str:
    #     import hashlib

    #     hash_object = str(hashlib.sha256(self.organization_id.encode()))[:63]
    #     hash_hex = hash_object.hexdigest()
    #     return f"https://s3.amazonaws.com/{hash_hex}/{self.path}"

    # # DEMO -> Application URL property --- This is an interesting one because it needs to conform via convention with the urls on the frontend.
    # @property
    # def application_url(self) -> str:
    #     from urllib.parse import quote

    #     encoded_path = quote(self.path)
    #     return f"https://app.driver.ai/{encoded_path}"

    # # Methods
    # # DEMO -> Our child checks can be on here. There may be a way to overload relationships so that it can traverse the path to get direct children.
    # def is_child(self, parent_node_or_path: Union["Node", str]) -> bool:
    #     if isinstance(parent_node_or_path, Node):
    #         return self.absolute_path.startswith(
    #             parent_node_or_path.absolute_path.rstrip("/") + "/"
    #         )
    #     elif isinstance(parent_node_or_path, str):
    #         return self.path.startswith(
    #             parent_node_or_path.rstrip("/") + "/"
    #         ) or self.absolute_path.startswith(parent_node_or_path.rstrip("/") + "/")

    def is_parent(self, child_node_or_path: Union["Node", str]) -> bool:
        if isinstance(child_node_or_path, Node):
            return child_node_or_path.absolute_path.startswith(
                self.absolute_path.rstrip("/") + "/"
            )
        elif isinstance(child_node_or_path, str):
            return child_node_or_path.startswith(
                (self.path.rstrip("/") + "/", self.absolute_path.rstrip("/") + "/")
            )

    # # Relationships
    # contents: list[ContentTableRow] = Relationship(
    #     back_populates="node",
    #     sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    # )
    # tags: list[TagTableRow] = Relationship(
    #     back_populates="nodes",
    #     sa_relationship_kwargs={"secondary": "node_tags"},
    # )

    # # DEMO -> children and parent can be loaded using sqlalchemy. Then we can build already authorized, topographical joins in python.
    # children: list[Self] = Relationship(
    #     back_populates="parent",
    #     sa_relationship_kwargs={
    #         "primaryjoin": "and_(Node.organization_id == foreign(Node.organization_id), Node.path.like(foreign(Node.path) + '/%'))",
    #         "cascade": "all, delete-orphan",
    #     },
    # )
    # parent: Optional[Self] = Relationship(
    #     back_populates="children",
    #     sa_relationship_kwargs={
    #         "primaryjoin": "and_(Node.organization_id == remote(Node.organization_id), Node.path.like(remote(Node.path) + '/%'))",
    #         "order_by": "func.length(Node.path).desc()",
    #         "uselist": False,
    #     },
    # )
    # ancestors: list[Self] = Relationship(
    #     sa_relationship_kwargs={
    #         "primaryjoin": "and_(Node.organization_id == remote(Node.organization_id), Node.path.like(remote(Node.path) + '/%'))",
    #         "order_by": "func.length(Node.path).desc()",
    #     },
    # )


# # DEMO: NodeDto for API interactions
# class NodeDto(BaseModel):
#     id: UUID | None
#     path: str
#     created_at: datetime | None
#     updated_at: datetime | None
#     node_type: str
#     display_name: str | None
#     organization_id: str | None
#     parent_node: Optional[Self] = None
#     child_nodes: list[Self] | None = None

#     @classmethod
#     def from_node(cls, node: Node) -> Self:
#         return cls(
#             id=node.id,
#             path=node.path,
#             created_at=node.created_at,
#             updated_at=node.updated_at,
#             node_type=node.node_type,
#             display_name=node.display_name,
#             organization_id=node.organization_id,
#             parent_node=cls.from_node(node.parent_node) if node.parent_node else None,
#             child_nodes=[cls.from_node(child) for child in node.child_nodes]
#             if node.child_nodes
#             else None,
#         )

#     def to_node(self) -> Node:
#         kwargs = {"path": self.path}
#         if self.id is not None:
#             kwargs["id"] = self.id
#         if self.display_name is not None:
#             kwargs["custom_display_name"] = self.display_name
#         if self.organization_id is not None:
#             kwargs["organization_id"] = self.organization_id
#         if self.created_at is not None:
#             kwargs["created_at"] = self.created_at
#         if self.updated_at is not None:
#             kwargs["updated_at"] = self.updated_at
#         node = Node(**kwargs)

#         return node
