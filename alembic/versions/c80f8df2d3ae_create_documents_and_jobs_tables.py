"""create documents and jobs tables

Revision ID: c80f8df2d3ae
Revises: a1b3fd93b2f8
Create Date: 2025-09-22 11:14:02.206739

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c80f8df2d3ae'
down_revision: Union[str, Sequence[str], None] = 'a1b3fd93b2f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
