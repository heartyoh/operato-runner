"""remove_is_public_column

Revision ID: 9b9ad181c3d9
Revises: d6ea828b344d
Create Date: 2025-06-29 16:56:02.340130

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b9ad181c3d9'
down_revision: Union[str, None] = 'd6ea828b344d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
