"""merge heads

Revision ID: 213b41036992
Revises: 44a2273a47b2
Create Date: 2025-06-29 14:20:28.939851

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '213b41036992'
down_revision: Union[str, None] = '44a2273a47b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
