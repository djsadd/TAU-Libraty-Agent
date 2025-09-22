"""probe

Revision ID: 4c5563f0db35
Revises: 61c2408c26d5
Create Date: 2025-09-22 11:15:35.882609

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c5563f0db35'
down_revision: Union[str, Sequence[str], None] = '61c2408c26d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
