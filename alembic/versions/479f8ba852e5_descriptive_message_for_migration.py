"""Descriptive message for migration

Revision ID: 479f8ba852e5
Revises: 927c05bbc7fd
Create Date: 2025-10-27 12:31:41.860317

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '479f8ba852e5'
down_revision: Union[str, Sequence[str], None] = '927c05bbc7fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
