"""remove_is_public_column

Revision ID: a7e74db8eefd
Revises: 9b9ad181c3d9
Create Date: 2025-06-29 16:56:23.573160

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7e74db8eefd'
down_revision: Union[str, None] = '9b9ad181c3d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
