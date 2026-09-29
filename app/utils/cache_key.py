import hashlib
import json
from uuid import UUID

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

    serialized_filters = json.dumps(
        filters,
        sort_keys=True,
        separators=(",", ":"),
    )

    filter_hash = hashlib.sha256(serialized_filters.encode("UTF-8")).hexdigest()

    return f"{CacheKeyConstants.CATEGORY_LIST_PREFIX}:{filter_hash}"


def build_product_list_cache_key(
    *,
    search: str | None = None,
    category_name: str | None = None,
    status: str | None = None,
    min_price: str | None = None,
    max_price: str | None = None,
    in_stock: bool | None = None,
    sort_by: str,
    sort_order: str = "desc",
    page: int,
    page_size: int,
):

    filters = {
        "search": search,
        "category_name": category_name,
        "status": status,
        "min_price": min_price,
        "max_price": max_price,
        "in_stock": in_stock,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "page": page,
        "page_size": page_size,
    }

    serialized_filters = json.dumps(
        filters,
        sort_keys=True,
        separators=(",", ":"),
    )

    filter_hash = hashlib.sha256(serialized_filters.encode("UTF-8")).hexdigest()

    return f"{CacheKeyConstants.PRODUCT_LIST_CACHE_PREFIX}:{filter_hash}"


def build_product_cache_key(id: UUID) -> str:
    return f"{CacheKeyConstants.PRODUCT_CACHE_PREFIX}{id}"
