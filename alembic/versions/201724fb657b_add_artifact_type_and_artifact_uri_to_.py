"""add artifact_type and artifact_uri to modules

Revision ID: 201724fb657b
Revises: 97821c09642f
Create Date: 2025-05-25 14:31:05.511842

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '201724fb657b'
down_revision: Union[str, None] = '97821c09642f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # modules 테이블에 artifact_type, artifact_uri 컬럼만 추가
    op.add_column('modules', sa.Column('artifact_type', sa.String(length=20), nullable=True))
    op.add_column('modules', sa.Column('artifact_uri', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # modules 테이블에서 artifact_type, artifact_uri 컬럼만 삭제
    op.drop_column('modules', 'artifact_uri')
    op.drop_column('modules', 'artifact_type')
