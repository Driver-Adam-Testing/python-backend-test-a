import asyncio

from workflows.inspector_workflow import InspectorInput, inspector_task


async def main() -> None:
    inspect_result = await inspector_task.aio_run(
        InspectorInput(version_id="b783d8c0-063f-47c6-8700-ee983db8ce7a")
        # InspectorInput(version_id="580ff146-0049-4286-9c76-bf1a734e9cb1")
    )
    print("Inspector task result:", inspect_result)
    # auth0_result = auth0_sync_task.run(
    #     Auth0SyncInput(dry_run=True, verbose=True, initial_run=False)
    # )


if __name__ == "__main__":
    asyncio.run(main())
