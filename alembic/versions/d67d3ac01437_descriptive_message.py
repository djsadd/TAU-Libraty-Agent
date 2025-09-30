"""descriptive message

Revision ID: d67d3ac01437
Revises: 4f937a8097f9
Create Date: 2025-09-26 16:51:12.970532

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd67d3ac01437'
down_revision: Union[str, Sequence[str], None] = '4f937a8097f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
