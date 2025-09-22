"""probe

Revision ID: 29cf6a2eee52
Revises: 4c5563f0db35
Create Date: 2025-09-22 11:17:04.632644

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '29cf6a2eee52'
down_revision: Union[str, Sequence[str], None] = '4c5563f0db35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
