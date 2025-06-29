"""change_is_public_to_visibility

Revision ID: d7d134cf12e1
Revises: 213b41036992
Create Date: 2025-06-29 16:46:26.370537

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7d134cf12e1'
down_revision: Union[str, None] = '213b41036992'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # visibility 컬럼이 이미 존재하므로 데이터 마이그레이션만 수행
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE modules 
        SET visibility = CASE 
            WHEN is_public = 1 THEN 'public' 
            ELSE 'private' 
        END
        WHERE visibility IS NULL
    """))


def downgrade() -> None:
    """Downgrade schema."""
    # 데이터를 원래대로 되돌리기
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE modules 
        SET visibility = NULL
    """))
