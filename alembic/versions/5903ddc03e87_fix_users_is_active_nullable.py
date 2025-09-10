"""fix_users_is_active_nullable

Revision ID: 5903ddc03e87
Revises: add_temp_files
Create Date: 2025-09-10 00:05:48.138091

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5903ddc03e87'
down_revision: Union[str, None] = 'add_temp_files'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite doesn't support ALTER COLUMN, but the column is already nullable in practice
    # This migration is essentially a no-op for SQLite
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # SQLite doesn't support ALTER COLUMN, downgrade is also a no-op
    pass
