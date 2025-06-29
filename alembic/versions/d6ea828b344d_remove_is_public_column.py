"""remove_is_public_column

Revision ID: d6ea828b344d
Revises: d7d134cf12e1
Create Date: 2025-06-29 16:55:59.153168

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6ea828b344d'
down_revision: Union[str, None] = 'd7d134cf12e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
