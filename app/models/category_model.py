from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import BaseEntity

if TYPE_CHECKING:
    from app.models.product_model import Product


class Category(BaseEntity):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    avatar_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="category",
    )
