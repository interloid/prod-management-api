import hashlib
import json
from typing import Any


def generate_etag(data: Any) -> str:
    seralized_data = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
    )

    etag = hashlib.sha256(seralized_data.encode("utf-8")).hexdigest()

    return f'"{etag}"'
