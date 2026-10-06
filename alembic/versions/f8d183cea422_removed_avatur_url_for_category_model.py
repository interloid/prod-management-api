"""removed avatur_url for category model

Revision ID: f8d183cea422
Revises: 13d36bf4456f
Create Date: 2026-10-06 10:57:14.413533

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f8d183cea422'
down_revision: Union[str, None] = '13d36bf4456f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('categories', 'avatar_url')


def downgrade() -> None:
    op.add_column('categories', sa.Column('avatar_url', sa.TEXT(), autoincrement=False, nullable=True))
