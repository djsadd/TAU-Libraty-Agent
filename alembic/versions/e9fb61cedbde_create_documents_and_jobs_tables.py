"""create documents and jobs tables

Revision ID: e9fb61cedbde
Revises: 36b0e3828540
Create Date: 2025-09-22 10:29:49.416189

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9fb61cedbde'
down_revision: Union[str, Sequence[str], None] = '36b0e3828540'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
