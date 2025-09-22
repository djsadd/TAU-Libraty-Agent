"""create documents and jobs tables

Revision ID: c3f3de486dcb
Revises: a7925c5a9d6d
Create Date: 2025-09-22 11:05:44.892705

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3f3de486dcb'
down_revision: Union[str, Sequence[str], None] = 'a7925c5a9d6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
