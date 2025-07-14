"""Add is_active column to user table

Revision ID: d75cf45ba241
Revises: 264e6234169e
Create Date: 2025-07-14 21:59:57.333168

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd75cf45ba241'
down_revision: Union[str, None] = '264e6234169e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade() -> None:
    op.drop_column('users', 'is_active')
