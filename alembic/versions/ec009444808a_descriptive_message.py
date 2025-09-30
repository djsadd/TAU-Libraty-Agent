"""descriptive message

Revision ID: ec009444808a
Revises: d67d3ac01437
Create Date: 2025-09-26 16:56:41.682397

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec009444808a'
down_revision: Union[str, Sequence[str], None] = 'd67d3ac01437'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("kabis", sa.Column("file_is_index", sa.Boolean(), nullable=True, server_default=sa.false()))

def downgrade() -> None:
    op.drop_column("kabis", "file_is_index")