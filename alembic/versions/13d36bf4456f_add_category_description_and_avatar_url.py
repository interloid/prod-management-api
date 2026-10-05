"""add category description and avatar url

Revision ID: 13d36bf4456f
Revises: 06240db0f3e2
Create Date: 2026-10-05 18:14:37.436387

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '13d36bf4456f'
down_revision: Union[str, None] = '06240db0f3e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "categories",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.add_column(
        "categories",
        sa.Column("avatar_url", sa.Text(), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_column('categories', 'avatar_url')
    op.drop_column('categories', 'description')
