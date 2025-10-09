"""create library

Revision ID: 0da8d0a2ea86
Revises: d43e9cc48cf9
Create Date: 2025-10-09 15:59:49.313204

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0da8d0a2ea86'
down_revision: Union[str, Sequence[str], None] = 'd43e9cc48cf9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
