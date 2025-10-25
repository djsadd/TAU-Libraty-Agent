"""Description of migration

Revision ID: 7999665ab65e
Revises: 179892a91e90
Create Date: 2025-10-25 11:03:27.010815

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7999665ab65e'
down_revision: Union[str, Sequence[str], None] = '179892a91e90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
