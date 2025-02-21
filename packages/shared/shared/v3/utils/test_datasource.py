PAGE_IDS = [
    "78e7c48b-583a-44ff-bf81-afb8393cc1ea",
]

NODE_IDS = [
    "e18b43e0-3d69-4f71-9fa0-1047f6885230",
]


def main():
    from uuid import UUID

    from shared.v3.utils.datasource import DataSource

    print("\n===== Test: from_node_ids =====")
    ds1 = DataSource.from_node_ids(
        node_ids=[UUID("e18b43e0-3d69-4f71-9fa0-1047f6885230")],
        organization_id="org_s76pU1v8LAYhTOWB",
    )
    print(ds1.human_readable_summary())
    input()
    print("\n===== Test: from_page_id (may require a valid database setup) =====")
    try:
        ds2 = DataSource.from_page_id(
            page_node_id=UUID("78e7c48b-583a-44ff-bf81-afb8393cc1ea"),
            organization_id="org_s76pU1v8LAYhTOWB",
        )
        print("DataSource 2:")
        print(f"  node_ids: {ds2.node_ids}")
        print(f"  organization_id: {ds2.organization_id}")
    except Exception as exc:
        print(f"from_page_id failed as expected if DB not set up: {exc}")
    print("------")

    print("\n===== Test: narrow method (may require valid Nodes in the DB) =====")
    try:
        # Provide sample identifiers to narrow
        narrowed_ds = ds1.narrow(
            requested_identifiers=["/src/auth", "MyAsset@v7/src/auth"]
        )
        print("Narrowed DataSource:")
        print(f"  node_ids: {narrowed_ds.node_ids}")
    except Exception as exc:
        print(f"narrow failed as expected if DB not set up: {exc}")
    print("------")


if __name__ == "__main__":
    main()
