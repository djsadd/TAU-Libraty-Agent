"""create documents and jobs tables

Revision ID: 4d933d534c55
Revises: ab8c467fbd9d
Create Date: 2025-09-22 10:35:04.166820

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d933d534c55'
down_revision: Union[str, Sequence[str], None] = 'ab8c467fbd9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
