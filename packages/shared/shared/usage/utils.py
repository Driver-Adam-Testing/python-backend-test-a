CONVERSION_FACTOR = 50


def bytes_to_sloc(bytes: int) -> int:
    return abs(bytes) // CONVERSION_FACTOR


def sloc_to_bytes(sloc: int) -> int:
    return sloc * CONVERSION_FACTOR
