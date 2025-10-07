"""description of migration

Revision ID: 89948769fd17
Revises: f36f881182df
Create Date: 2025-10-07 16:05:10.831675

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89948769fd17'
down_revision: Union[str, Sequence[str], None] = 'f36f881182df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
