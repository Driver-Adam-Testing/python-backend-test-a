from uuid import UUID

from shared.v3.utils.datasource import DataSource


def test_data_source_from_version_node_ids() -> None:
    """
    Basic test for DataSource.from_version_node_ids
    Ensures we can create a DataSource from a list of version_node_ids and an organization_id.
    """
    version_node_ids = [UUID("00000000-0000-0000-0000-000000000000")]
    organization_id = "test_org"
    ds = DataSource.from_version_node_ids(version_node_ids=version_node_ids, organization_id=organization_id)

    assert ds.version_node_ids == version_node_ids
    assert ds.organization_id == organization_id


def test_data_source_from_page_id() -> None:
    """
    Basic test for DataSource.from_page_id
    This will only check that the method can be called
    and returns an instance of DataSource. Actual DB calls cannot be tested here.
    """
    page_version_node_id = UUID("11111111-1111-1111-1111-111111111111")
    organization_id = "test_org"
    ds = DataSource.from_page_id(
        page_version_node_id=page_version_node_id, organization_id=organization_id
    )

    assert ds.organization_id == organization_id


def test_data_source_constructor() -> None:
    """
    Test that we can construct a DataSource with version_node_ids directly.
    This tests the constructor without requiring database calls.
    """
    version_node_ids = [UUID("22222222-2222-2222-2222-222222222222")]
    organization_id = "test_org"

    ds = DataSource(version_node_ids=version_node_ids, organization_id=organization_id)
    assert ds.version_node_ids == version_node_ids
    assert ds.organization_id == organization_id
