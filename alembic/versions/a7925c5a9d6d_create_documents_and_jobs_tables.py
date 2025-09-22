"""create documents and jobs tables

Revision ID: a7925c5a9d6d
Revises: 4d933d534c55
Create Date: 2025-09-22 10:36:20.850334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7925c5a9d6d'
down_revision: Union[str, Sequence[str], None] = '4d933d534c55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
