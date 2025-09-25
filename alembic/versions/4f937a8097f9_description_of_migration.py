"""Description of migration

Revision ID: 4f937a8097f9
Revises: 956b7f5e4a94
Create Date: 2025-09-25 14:45:17.297730

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f937a8097f9'
down_revision: Union[str, Sequence[str], None] = '956b7f5e4a94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
