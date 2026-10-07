from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.exceptions import RequestValidationError
from pydantic import TypeAdapter, ValidationError

from app.api.authorization import require_permission
from app.api.dependencies import get_cache_service, get_product_service
from app.core.constants import (
    CacheKeyConstants,
    PaginationEnum,
    PermissionEnum,
    ProductStatusEnum,
)
from app.core.logging import get_logger
from app.core.rate_limiter import enforce_read_rate_limit, enforce_write_rate_limit
from app.core.s3 import S3Service, get_s3_service
from app.exceptions.custom import BadRequestException
from app.exceptions.global_exception import CRUD_ERROR_RESPONSES
from app.models.product_model import Product
from app.schemas.product_image_schema import ProductImageResponse
from app.schemas.product_schema import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from app.schemas.response import (
    ApiResponse,
    PaginatedResponse,
    PaginationMeta,
)
from app.services.cache_service import CacheService
from app.services.product_service import ProductService
from app.utils.cache_key import build_product_cache_key, build_product_list_cache_key
from app.utils.etag import generate_etag

logger = get_logger(__name__)

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


def build_product_response(
    product: Product,
    image_urls: dict[str, str],
) -> ProductResponse:

    ordered_images = sorted(
        product.images,
        key=lambda image: (
            not image.is_primary,
            image.created_at,
            str(image.id),
        ),
    )

    return ProductResponse(
        id=product.id,
        name=product.name,
        sku=product.sku,
        category_name=product.category.name,
        price=product.price,
        stock=product.stock,
        status=ProductStatusEnum(product.status),
        description=product.description,
        images=[
            ProductImageResponse(
                id=image.id,
                url=image_urls[image.object_key],
                is_primary=image.is_primary,
            )
            for image in ordered_images
        ],
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


async def to_product_responses(
    products: list[Product],
    s3_service: S3Service,
) -> list[ProductResponse]:

    responses: list[ProductResponse] = []

    for product in products:
        cloudfront_url = await s3_service.generate_cloudfront_urls(
            object_keys=[image.object_key for image in product.images],
        )

        responses.append(
            build_product_response(
                product=product,
                image_urls=cloudfront_url,
            )
        )

    return responses


async def to_product_response(
    product: Product,
    s3_service: S3Service,
) -> ProductResponse:

    cloudfront_urls = await s3_service.generate_cloudfront_urls(
        object_keys=[image.object_key for image in product.images],
    )

    return build_product_response(
        product=product,
        image_urls=cloudfront_urls,
    )


@router.post(
    "",
    dependencies=[
        Depends(require_permission(PermissionEnum.CREATE_PRODUCTS)),
        Depends(enforce_write_rate_limit),
    ],
    response_model=ApiResponse[ProductResponse],
    status_code=status.HTTP_202_ACCEPTED,
    responses=CRUD_ERROR_RESPONSES,
)
async def create_product(
    request: Request,
    name: Annotated[str, Form(...)],
    sku: Annotated[str, Form(...)],
    category_name: Annotated[str, Form(...)],
    price: Annotated[Decimal, Form(...)],
    stock: Annotated[int, Form(...)],
    product_status: Annotated[ProductStatusEnum | None, Form(alias="status")] = None,
    description: Annotated[str | None, Form()] = None,
    images: Annotated[list[UploadFile] | None, File()] = None,
    product_service: ProductService = Depends(get_product_service),
) -> ApiResponse[None]:

    try:
        payload = ProductCreate(
            name=name,
            sku=sku,
            category_name=category_name,
            price=price,
            stock=stock,
            status=product_status,
            description=description,
        )

    except ValidationError as exc:
        raise RequestValidationError(
            exc.errors(),
        ) from exc

    request_id = request.state.request_id

    await product_service.create_product(
        payload=payload,
        images=images or [],
        request_id=request_id,
    )

    return ApiResponse(message="Product created successfully")


@router.get(
    "",
    dependencies=[
        Depends(require_permission(PermissionEnum.VIEW_PRODUCTS)),
        Depends(enforce_read_rate_limit),
    ],
    response_model=PaginatedResponse[ProductResponse],
    status_code=status.HTTP_200_OK,
    responses=CRUD_ERROR_RESPONSES,
)
async def list_products(
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    category_name: str | None = Query(
        default=None,
        min_length=1,
        max_length=255,
    ),
    status_filter: ProductStatusEnum | None = Query(
        default=None,
        alias="status",
    ),
    min_price: Decimal | None = Query(
        default=None,
        ge=0,
    ),
    max_price: Decimal | None = Query(
        default=None,
        ge=0,
    ),
    in_stock: bool | None = Query(
        default=None,
    ),
    sort: str = Query(
        default="updated",
        min_length=1,
        max_length=50,
    ),
    order: str = Query(
        default="desc",
        min_length=1,
        max_length=4,
    ),
    page: int = Query(
        default=PaginationEnum.DEFAULT_PAGE,
        ge=1,
    ),
    page_size: int = Query(
        default=PaginationEnum.DEFAULT_PAGE_SIZE,
        ge=1,
        le=PaginationEnum.MAX_PAGE_SIZE,
    ),
    product_service: ProductService = Depends(get_product_service),
    cache: CacheService = Depends(get_cache_service),
    s3_service: S3Service = Depends(get_s3_service),
) -> PaginatedResponse[ProductResponse]:

    if min_price is not None and max_price is not None and min_price > max_price:
        logger.warning(
            "Minimum price cannot be greater than maximum price | "
            "min_price=%s | max_price=%s",
            min_price,
            max_price,
        )
        raise BadRequestException(
            message="Minimum price cannot be greater than maximum price",
        )

    cached_key = build_product_list_cache_key(
        search=search.strip() if search else None,
        category_name=category_name,
        status=status_filter.value if status_filter else None,
        min_price=str(min_price) if min_price is not None else None,
        max_price=str(max_price) if max_price is not None else None,
        in_stock=in_stock,
        sort_by=sort,
        sort_order=order,
        page=page,
        page_size=page_size,
    )

    cached_data = await cache.get_json(cached_key)

    if cached_data is not None:
        logger.info("product list cached data", extra={"cached_key": cached_key})
        return PaginatedResponse[ProductResponse](**cached_data)

    products, total = await product_service.list_products(
        search=search.strip() if search else None,
        category_name=category_name,
        status=status_filter,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        sort_by=sort,
        sort_order=order,
        page=page,
        page_size=page_size,
    )

    items = await to_product_responses(
        products=products,
        s3_service=s3_service,
    )

    total_pages = product_service.calculate_total_pages(
        total=total,
        page_size=page_size,
    )

    response = PaginatedResponse(
        message="Products retrieved successfully",
        data=items,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
    )

    await cache.set_json(
        key=cached_key,
        value=response.model_dump(mode="json"),
        ttl=60,
    )

    await cache.add_to_set(
        key=CacheKeyConstants.PRODUCT_LIST_CACHE_KEYS,
        value=cached_key,
    )

    return response


@router.get(
    "/{id}",
    dependencies=[
        Depends(require_permission(PermissionEnum.VIEW_PRODUCTS)),
        Depends(enforce_read_rate_limit),
    ],
    response_model=ApiResponse[ProductResponse],
    status_code=status.HTTP_200_OK,
    responses=CRUD_ERROR_RESPONSES,
)
async def get_product(
    id: UUID,
    http_response: Response,
    if_none_match: str | None = Header(default=None),
    product_service: ProductService = Depends(get_product_service),
    s3_service: S3Service = Depends(get_s3_service),
    cache: CacheService = Depends(get_cache_service),
) -> ApiResponse[ProductResponse]:

    cached_key = build_product_cache_key(id=id)

    cached_data = await cache.get_json(cached_key)

    if cached_data is not None:
        logger.info("product cached data", extra={"cached_key": cached_key})
        cached_etag = generate_etag(cached_data)

        http_response.headers["ETag"] = cached_etag

        if if_none_match == cached_etag:
            http_response.status_code = status.HTTP_304_NOT_MODIFIED
            return Response(status_code=status.HTTP_304_NOT_MODIFIED)

        return ApiResponse[ProductResponse](**cached_data)

    product = await product_service.get_product(
        product_id=id,
    )

    response = ApiResponse(
        message="Product retrieved successfully",
        data=await to_product_response(
            product=product,
            s3_service=s3_service,
        ),
    )

    response_json = response.model_dump(mode="json")

    etag = generate_etag(response_json)

    await cache.set_json(
        key=cached_key,
        value=response_json,
        ttl=300,
    )

    http_response.headers["ETag"] = etag

    if if_none_match == etag:
        http_response.status_code = status.HTTP_304_NOT_MODIFIED
        return Response(
            status_code=status.HTTP_304_NOT_MODIFIED, headers={"ETag": cached_etag}
        )

    return response


removed_image_ids_adapter = TypeAdapter(list[UUID])


def parse_removed_image_ids(
    value: str | None,
) -> list[UUID] | None:
    if not value:
        return None

    try:
        return removed_image_ids_adapter.validate_json(value)

    except ValidationError as exc:
        errors = []

        for error in exc.errors():
            errors.append(
                {
                    **error,
                    "loc": (
                        "body",
                        "removed_image_ids",
                        *error["loc"],
                    ),
                }
            )

        raise RequestValidationError(errors) from exc


@router.patch(
    "/{id}",
    dependencies=[
        Depends(require_permission(PermissionEnum.UPDATE_PRODUCTS)),
        Depends(enforce_write_rate_limit),
    ],
    response_model=ApiResponse[ProductResponse],
    status_code=status.HTTP_200_OK,
    responses=CRUD_ERROR_RESPONSES,
)
async def update_product(
    request: Request,
    id: UUID,
    name: Annotated[str | None, Form()] = None,
    sku: Annotated[str | None, Form()] = None,
    category_name: Annotated[str | None, Form()] = None,
    price: Annotated[Decimal | None, Form()] = None,
    stock: Annotated[int | None, Form()] = None,
    product_status: Annotated[ProductStatusEnum | None, Form(alias="status")] = None,
    description: Annotated[str | None, Form()] = None,
    removed_image_ids: Annotated[str | None, Form()] = None,
    primary_image_id: Annotated[UUID | None, Form()] = None,
    images: Annotated[list[UploadFile] | None, File()] = None,
    product_service: ProductService = Depends(get_product_service),
    s3_service: S3Service = Depends(get_s3_service),
) -> ApiResponse[ProductResponse]:

    parsed_removed_image_ids = parse_removed_image_ids(
        removed_image_ids,
    )
    if (
        primary_image_id is not None
        and parsed_removed_image_ids
        and primary_image_id in parsed_removed_image_ids
    ):
        raise BadRequestException(
            message="Primary image cannot also be removed",
        )

    payload_data = {
        field: value
        for field, value in {
            "name": name,
            "sku": sku,
            "category_name": category_name,
            "price": price,
            "stock": stock,
            "status": product_status,
            "description": description,
        }.items()
        if value is not None
    }

    try:
        payload = ProductUpdate(**payload_data)
    except ValidationError as exc:
        raise RequestValidationError(
            exc.errors(),
        ) from exc

    request_id = request.state.request_id

    product = await product_service.update_product(
        product_id=id,
        payload=payload,
        images=images or [],
        removed_image_ids=parsed_removed_image_ids,
        primary_image_id=primary_image_id,
        request_id=request_id,
    )

    return ApiResponse(
        message="Product updated successfully",
        data=await to_product_response(
            product=product,
            s3_service=s3_service,
        ),
    )


@router.delete(
    "/{id}",
    dependencies=[
        Depends(require_permission(PermissionEnum.DELETE_PRODUCTS)),
        Depends(enforce_write_rate_limit),
    ],
    status_code=status.HTTP_204_NO_CONTENT,
    responses=CRUD_ERROR_RESPONSES,
)
async def delete_product(
    request: Request,
    id: UUID,
    product_service: ProductService = Depends(get_product_service),
) -> Response:

    request_id = request.state.request_id

    await product_service.delete_product(
        product_id=id,
        request_id=request_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
