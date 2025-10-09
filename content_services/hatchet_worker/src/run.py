import asyncio

from workflows.first_workflow import my_task
from workflows.pdf_processing_workflow import PDFProcessingInput, pdf_processing_task


async def main() -> None:
    result = await my_task.aio_run()
    print("running pdf processing task")
    pdf_result = await pdf_processing_task.aio_run(
        PDFProcessingInput(
            presigned_url="https://6b00f9ade1094692d388c5dc385d7dccc474504aa5778cb5389f732f36ef641.s3.us-east-1.amazonaws.com/cedc4474-e4fe-4c88-90bf-c52614d973b9/9057c7aa-4777-453e-9f6e-4747944aa36d/__unsanitized.pdf?response-content-disposition=inline&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEC8aCXVzLWVhc3QtMSJGMEQCIHeCFzzmyk76KMb7JjS7ka5PKGWWm%2FrYIIkn0%2B1boW0sAiBswwcSu5aMGcczr7Wbw3My%2FQoVOLEHT5qey2L6Y0ii5Cq%2BBAjI%2F%2F%2F%2F%2F%2F%2F%2F%2F%2F8BEAEaDDU1MDA4Mjc2MTEwOSIMx4KuXUiGdgyblSyFKpIE8b9859X6E4Lg0IArdHXn%2FANrMNWgFd%2Bt3OBE58%2B4zDWDEj6xfRH%2B1PimCWBnVSlHntW9NYVnTNGsNq%2BnjdZYg7P0ezLnY%2F4hVci1TjSkoFJn768tPHiWglYWem4ynLZhw95hJcsW%2Bs0G0cCZkMDSsNAG39s55ALfUHgaJzWRi7eRWeqRAlzaQyW29ucpHMBW9z7c8GtiJXOvkWR8w%2FHijUbjz0C0i2oVyqc3vc3OufmDmhuXvOGZXh4QYogEicsNrl1BrVhsg%2BmMmtaJUV0qavAvaHzQwWVWTapEiDJ7s5K0FJveWFqv0LotvIkku9uF7QD0jCCsCG1KhQOjQCml3yPOERC3V7HiqrPB%2BEoT8K4z5lr9TCHEFjGMTGUu91FKfMir%2FnrhX7A%2BNNZt70OspK9YXrkZWJUP2KAz4Y%2BHMzBXIqqwtrzZLk19g5F6ssQxpHwaJwgbtwF%2FiHC3PWn1%2FRDycSnAXg8M9G8tZg24nuXA6qkWwQN%2Fo6IRZMq3IOhnuVPQbfy46vVxElBHXQZa3%2BbBxRr8H4vTDELJ1H6ndsYdTNixrLFiAA%2FO7lFifYWY5ELvmtGRol%2FXRHGOQ0HeqI%2FAahaOcF5KNS9YApTBe2wT25%2B4mcWHiIl%2B3hIRtkupC8ei37%2FpGmi1PV%2FpdaSeYOt1vvt5C8WGJChMbmK9XsIescebXibpOguVLoQk1bDOhWMwuaWbxwY6xgJwK7zYyigeR6txniuNVkX0%2B85aH3wx5SbTPZuCvMTBH5VCpFjqLNHZHcJLHNofosFQpFhzLF2rxM5LJYNKAwgB6Hgfk9eI1QnymAw1LJRHWU123YxbfQFqRGcEwky0R17xffENzA2nvkrnw9Uu%2FVWdu1lmWeD16OoSUhXJnfAzV1DvSto6fI7XZ6n6BmZnMpYhyn2qyxx4pQN9rc7F2bL01R%2FBRGbJQH8iAEPGki1wqmEGKlZIggRXH%2Bis1wx%2FYCD4vZ0gaFRpSuFOUXsptEWHh03W1wdeQp5kk7CgNrmHmbVRO8T1n%2B82FK14bxeZUjsgFXaUmcVfug4UfysAcnG5bODn8qrJPl5KYyzn4LUn7JVi6MNbL0RC5BulnbLs695rbB2yMvLnRz4QN6xWgCFZyYI2Scp0EvcxaxunGRWC16YjYEGy1Q%3D%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIAYAE342GK46D5VAF4%2F20251008%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20251008T225823Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=88cc66905d73757d8e52156d5c034ff5ba57053742ed3c01a835f1d4f4a2df9d",
            version_id="9057c7aa-4777-453e-9f6e-4747944aa36d",
            asset_name="ade7913.pdf",
            org_id="org_s76pU1v8LAYhTOWB",
        )
    )
    print(
        "Finished running tasks. The meaning of life is:",
        result["meaning_of_life"],
    )
    print(
        "PDF processing task result:",
        pdf_result["status"],
    )


if __name__ == "__main__":
    asyncio.run(main())
