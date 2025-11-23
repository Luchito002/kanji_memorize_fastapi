"""Merge multiple heads

Revision ID: b266ebeae88c
Revises: 0c157db4cfde, add_rol_column_to_user
Create Date: 2025-11-23 18:51:05.145409

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b266ebeae88c'
down_revision: Union[str, None] = ('0c157db4cfde', 'add_rol_column_to_user')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
