import contextlib
import json
import uuid


class UUIDEncoder(json.JSONEncoder):
    def default(self, o: any) -> any:
        if isinstance(o, uuid.UUID):
            return str(o)
        return super().default(o)


def uuid_decoder_hook(dct: dict[str, any]) -> any:
    for key, value in dct.items():
        if isinstance(value, str):
            with contextlib.suppress(ValueError):
                dct[key] = uuid.UUID(value)
    return dct
