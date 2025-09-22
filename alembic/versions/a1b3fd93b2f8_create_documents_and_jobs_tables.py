"""create documents and jobs tables

Revision ID: a1b3fd93b2f8
Revises: c3f3de486dcb
Create Date: 2025-09-22 11:06:56.280624

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b3fd93b2f8'
down_revision: Union[str, Sequence[str], None] = 'c3f3de486dcb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
