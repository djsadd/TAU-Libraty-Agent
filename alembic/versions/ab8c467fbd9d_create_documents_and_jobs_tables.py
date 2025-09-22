"""create documents and jobs tables

Revision ID: ab8c467fbd9d
Revises: a64f790c3dc6
Create Date: 2025-09-22 10:34:21.477868

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab8c467fbd9d'
down_revision: Union[str, Sequence[str], None] = 'a64f790c3dc6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
