"""description of migration

Revision ID: dae53ee81fee
Revises: 5c9abcdfdde4
Create Date: 2025-10-07 16:03:15.845319

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dae53ee81fee'
down_revision: Union[str, Sequence[str], None] = '5c9abcdfdde4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
