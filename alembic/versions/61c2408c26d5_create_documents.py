"""create documents

Revision ID: 61c2408c26d5
Revises: c80f8df2d3ae
Create Date: 2025-09-22 11:14:10.512430

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61c2408c26d5'
down_revision: Union[str, Sequence[str], None] = 'c80f8df2d3ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
