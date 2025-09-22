"""create documents and jobs tables

Revision ID: a64f790c3dc6
Revises: e9fb61cedbde
Create Date: 2025-09-22 10:32:49.831286

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a64f790c3dc6'
down_revision: Union[str, Sequence[str], None] = 'e9fb61cedbde'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
