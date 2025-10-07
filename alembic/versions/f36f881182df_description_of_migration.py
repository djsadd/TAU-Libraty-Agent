"""description of migration

Revision ID: f36f881182df
Revises: dae53ee81fee
Create Date: 2025-10-07 16:04:37.077413

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f36f881182df'
down_revision: Union[str, Sequence[str], None] = 'dae53ee81fee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
