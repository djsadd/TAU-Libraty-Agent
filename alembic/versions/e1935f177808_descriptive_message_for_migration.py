"""Descriptive message for migration

Revision ID: e1935f177808
Revises: 479f8ba852e5
Create Date: 2025-10-27 12:33:48.153148

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1935f177808'
down_revision: Union[str, Sequence[str], None] = '479f8ba852e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
