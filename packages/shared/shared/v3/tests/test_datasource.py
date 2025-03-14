from uuid import UUID

from database.models_v1 import Tag  # noqa: F401
from shared.v3.utils.datasource import DataSource


def test_data_source_from_node_ids() -> None:
    """
    Basic test for DataSource.from_node_ids
    Ensures we can create a DataSource from a list of node_ids and an organization_id.
    """
    node_ids = [UUID("00000000-0000-0000-0000-000000000000")]
    organization_id = "test_org"
    ds = DataSource.from_node_ids(node_ids=node_ids, organization_id=organization_id)

    assert ds.node_ids == node_ids
    assert ds.organization_id == organization_id


def test_data_source_from_page_id() -> None:
    """
    Basic test for DataSource.from_page_id
    This will only check that the method can be called
    and returns an instance of DataSource. Actual DB calls cannot be tested here.
    """
    page_node_id = UUID("11111111-1111-1111-1111-111111111111")
    organization_id = "test_org"
    ds = DataSource.from_page_id(
        page_node_id=page_node_id, organization_id=organization_id
    )

    assert ds.organization_id == organization_id


def test_data_source_is_in_scope() -> None:
    """
    Check if is_in_scope returns True or False as expected in a trivial scenario.
    We will test a scenario where the child_path has a prefix with a slash.
    """
    ds = DataSource(node_ids=[], organization_id="test_org")

    # We will fake the _cached_nodes with one node that has a relative_path "docs"
    class FakeNode:
        relative_path = "docs"

    ds._cached_nodes = [FakeNode()]

    # child_path that starts with 'docs/'
    assert ds.is_in_scope("docs/somefile.md") is True
    # child_path that doesn't start with 'docs/'
    assert ds.is_in_scope("another/somefile.md") is False


def test_data_source_human_readable_summary() -> None:
    """
    Test human_readable_summary returns a string listing each node path.
    """
    ds = DataSource(node_ids=[], organization_id="test_org")

    class FakeNode:
        def __init__(self, path: str) -> None:
            self.relative_path = path

    ds._cached_nodes = [FakeNode("fileA.txt"), FakeNode("fileB.txt")]
    summary = ds.human_readable_summary()
    assert "- fileA.txt" in summary
    assert "- fileB.txt" in summary
