"""Descriptive message for migration

Revision ID: aa681a22d2ed
Revises: f46b5d17573b
Create Date: 2025-10-27 12:39:25.457513

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa681a22d2ed'
down_revision: Union[str, Sequence[str], None] = 'f46b5d17573b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
