"""add code and description to versions

Revision ID: 97821c09642f
Revises: 6ca4c9427802
Create Date: 2025-05-24 15:01:28.654531

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '97821c09642f'
down_revision: Union[str, None] = '6ca4c9427802'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # versions 테이블에 code, description 컬럼 추가만 남김
    op.add_column('versions', sa.Column('code', sa.Text(), nullable=True))
    op.add_column('versions', sa.Column('description', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # versions 테이블에서 code, description 컬럼만 삭제
    op.drop_column('versions', 'description')
    op.drop_column('versions', 'code')
