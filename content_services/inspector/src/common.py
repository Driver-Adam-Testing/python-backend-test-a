import modal

app = modal.App("inspector-v2")

volume = modal.Volume.from_name("my-volume")
MODAL_VOLUME_MOUNT_POINT = "/modal_volume"
