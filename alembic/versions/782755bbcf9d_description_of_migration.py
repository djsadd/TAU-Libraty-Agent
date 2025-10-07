"""description of migration

Revision ID: 782755bbcf9d
Revises: 1dd1c32051d7
Create Date: 2025-10-07 15:50:12.019786

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '782755bbcf9d'
down_revision: Union[str, Sequence[str], None] = '1dd1c32051d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
