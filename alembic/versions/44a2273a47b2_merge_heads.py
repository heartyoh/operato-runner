"""merge heads

Revision ID: 44a2273a47b2
Revises: 20240628_add_module_env_vars, 4144682c8993
Create Date: 2025-06-29 04:18:30.321663

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '44a2273a47b2'
down_revision: Union[str, None] = ('20240628_add_module_env_vars', '4144682c8993')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
