"""create library

Revision ID: e1b82dbbe70d
Revises: 0da8d0a2ea86
Create Date: 2025-10-09 16:07:14.253829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1b82dbbe70d'
down_revision: Union[str, Sequence[str], None] = '0da8d0a2ea86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
