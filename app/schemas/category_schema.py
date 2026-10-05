from uuid import UUID

from app.schemas.common import BaseSchema


class CategoryResponse(BaseSchema):
    id: UUID
    name: str
    description: str | None
    avatar_image: str | None
    total_products: int


class CategoryListResponse(BaseSchema):
    total_categories: int
    categories: list[CategoryResponse]
