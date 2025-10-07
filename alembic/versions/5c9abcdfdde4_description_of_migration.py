"""description of migration

Revision ID: 5c9abcdfdde4
Revises: 782755bbcf9d
Create Date: 2025-10-07 15:51:28.785337

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c9abcdfdde4'
down_revision: Union[str, Sequence[str], None] = '782755bbcf9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
