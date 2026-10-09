"""modify check constraint for price in product model

Revision ID: 21f11ee5c617
Revises: f8d183cea422
Create Date: 2026-10-09 11:08:01.045757

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '21f11ee5c617'
down_revision: Union[str, None] = 'f8d183cea422'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.drop_constraint("ck_products_price_non_negative", "products", type_="check")
    op.create_check_constraint("ck_products_price_min_one", "products", "price >= 1")


def downgrade() -> None:
    
    op.drop_constraint("ck_products_price_min_one", "products", type_="check")
    op.create_check_constraint("ck_products_price_non_negative", "products", "price >= 0")
    