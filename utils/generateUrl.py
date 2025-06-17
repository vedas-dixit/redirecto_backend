import hashlib
import base64

BASE62_CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def base62_encode(num: int) -> str:
    if num == 0:
        return BASE62_CHARS[0]
    res = ""
    while num > 0:
        res = BASE62_CHARS[num % 62] + res
        num //= 62
    return res


def generate_short_code(user_id: str, index: int) -> str:

    # Hash the user_id + index
    raw = f"{user_id}:{index}".encode("utf-8")
    hash_bytes = hashlib.sha256(raw).digest()

    # Take first 5-6 bytes to make it short
    short_int = int.from_bytes(hash_bytes[:6], byteorder="big")

    # Convert to base62
    short_code = base62_encode(short_int)

    return short_code
