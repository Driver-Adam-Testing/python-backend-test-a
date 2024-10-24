from collections import defaultdict

from database.models_v2 import Node

nodes = [
    Node(
        path="codebase1/",
        organization_id="org_s76pU1v8LAYhTOWB",
        version_id="version_1",
    ),
    Node(
        path="codebase1/app/",
        organization_id="org_s76pU1v8LAYhTOWB",
        version_id="version_1",
    ),
    Node(
        path="codebase1/app/auth/",
        organization_id="org_s76pU1v8LAYhTOWB",
        version_id="version_1",
    ),
    Node(
        path="codebase1/app/auth/auth.py",
        organization_id="org_s76pU1v8LAYhTOWB",
        version_id="version_1",
    ),
    Node(
        path="codebase1/",
        organization_id="org_s76pU1v8LAYhTOWB",
        version_id="version_2",
    ),
    Node(
        path="codebase1/app/",
        organization_id="org_s76pU1v8LAYhTOWB",
        version_id="version_2",
    ),
    Node(
        path="codebase1/app/auth/",
        organization_id="org_s76pU1v8LAYhTOWB",
        version_id="version_2",
    ),
    Node(
        path="codebase1/app/auth/auth.py",
        organization_id="org_s76pU1v8LAYhTOWB",
        version_id="version_2",
    ),
    Node(
        path="page_1.driver_page",
        organization_id="org_s76pU1v8LAYhTOWB",
        version_id=None,
        custom_display_name="Page Title Can Be Set Here",
    ),
    Node(
        path="page_2.driver_page",
        organization_id="org_s76pU1v8LAYhTOWB",
        version_id=None,
        prefix="workspace_folder",
        custom_display_name="A Page in a Folder",
    ),
    Node(
        path="12345678_1234_1234_12345678_schematics.pdf",
        organization_id="org_s76pU1v8LAYhTOWB",
        version_id=None,
        custom_display_name="schematics.pdf",
    ),
]

for node in nodes:
    input()
    print(f"\n\n\033[93m--- Persisted Properties ---\033[0m {node.display_name}\n")
    print("\033[93mNode ID:\033[0m", node.id)
    print("\033[93mPath:\033[0m", node.path)
    print("\033[93mCustom Display Name:\033[0m", node.custom_display_name)
    print("\033[93mOrganization ID:\033[0m", node.organization_id)
    print("\033[93mPrefix:\033[0m", node.prefix)
    print("\033[93mVersion ID:\033[0m", node.version_id)
    print("\033[93mCreated At:\033[0m", node.created_at)
    print("\033[93mUpdated At:\033[0m", node.updated_at)
    print("\n\033[93m--- Derived Properties ---\033[0m\n")
    print("\033[93mDisplay Name:\033[0m", node.display_name)
    print("\033[93mApplication URL:\033[0m", node.application_url)
    print("\033[93mAbsolute Path:\033[0m", node.absolute_path)
    print("\033[93mSource URL:\033[0m", node.source_url)
    print("\033[93mNode Type:\033[0m", node.node_type)
    print("\033[93mOrganization Hash:\033[0m", node.organization_hash)


def build_tree(paths: list[str]) -> defaultdict:
    def tree() -> any:
        return defaultdict(tree)

    root: any = tree()
    for path in paths:
        parts = path.strip("/").split("/")
        current_level = root
        for part in parts:
            current_level = current_level[part]
    return root


def print_tree(d: defaultdict, indent: int = 0) -> None:
    for key, subtree in sorted(d.items()):
        print("    " * indent + key)
        print_tree(subtree, indent + 1)


absolute_paths = [node.absolute_path for node in nodes]
tree_structure = build_tree(absolute_paths)

print("\n\033[93m--- Simulated 'ls' Tree Output ---\033[0m\n")
print_tree(tree_structure)
