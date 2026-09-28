import hashlib
import json

from app.core.constants import CacheKeyConstants


def build_category_list_cache_key(
    search: str | None,
    page: int,
    page_size: int,
) -> str:
    normalized_search = search.strip().lower() if search else None

    filters = {
        "search": normalized_search,
        "page": page,
        "page_size": page_size,
    }

    searlized_filters = json.dumps(
        filters,
        sort_keys=True,
        separators=(",", ":"),
    )

    filter_hash = hashlib.sha256(searlized_filters.encode("UTF-8")).hexdigest()

    return f"{CacheKeyConstants.CATEGORY_LIST_PREFIX}:{filter_hash}"
