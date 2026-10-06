from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.category_model import Category
from app.repositories.category_repo import CategoryRepository
from app.schemas.category_schema import CategoryResponse
from app.schemas.response import PaginatedResponse, PaginationMeta
from app.services.base_service import BaseService
from app.services.cache_service import CacheService
from app.utils.cache_key import build_category_list_cache_key

logger = get_logger(__name__)


class CategoryService(BaseService[Category]):
    def __init__(self, db: AsyncSession, cache: CacheService):
        super().__init__(db)
        self.category_repo = CategoryRepository(db=db)
        self.cache = cache

    async def get_categories(
        self,
        *,
        search: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedResponse[CategoryResponse]:

        self.validate_pagination(
            page=page,
            page_size=page_size,
        )

        cached_key = build_category_list_cache_key(
            search=search,
            page=page,
            page_size=page_size,
        )

        cached_data = await self.cache.get_json(cached_key)

        if cached_data is not None:
            logger.warning("categories cached data", extra={"cached_key": cached_key})
            return PaginatedResponse[CategoryResponse](**cached_data)

        category_stmt = self.category_repo.get_all(search=search)

        count_stmt = select(func.count()).select_from(
            category_stmt.order_by(None).subquery()
        )

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        offset = self.calculate_offset(
            page=page,
            page_size=page_size,
        )

        result = await self.db.execute(category_stmt.offset(offset).limit(page_size))

        categories = result.all()

        response = PaginatedResponse(
            message="Categories retrieved successfully",
            data=[
                CategoryResponse(
                    id=category.id,
                    name=category.name,
                    description=category.description,
                    total_products=total_products,
                )
                for category, total_products in categories
            ],
            pagination=PaginationMeta(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=self.calculate_total_pages(
                    total=total,
                    page_size=page_size,
                ),
            ),
        )

        await self.cache.set_json(
            key=cached_key,
            value=response.model_dump(mode="json"),
            ttl=300,
        )

        return response
