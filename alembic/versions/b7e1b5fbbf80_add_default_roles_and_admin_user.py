"""add default roles and admin user

Revision ID: b7e1b5fbbf80
Revises: b247dbb084dc
Create Date: 2025-05-23 02:50:56.759941

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e1b5fbbf80'
down_revision: Union[str, None] = 'b247dbb084dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 기본 role 데이터 삽입
    role_table = sa.table('roles',
        sa.column('id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('description', sa.Text),
    )
    op.bulk_insert(role_table, [
        {'id': 1, 'name': 'admin', 'description': '관리자'},
        {'id': 2, 'name': 'user', 'description': '일반 사용자'},
    ])
    # 기본 admin user 데이터 삽입 (비밀번호는 예시, 실제 운영시 해시 필요)
    user_table = sa.table('users',
        sa.column('id', sa.Integer),
        sa.column('username', sa.String),
        sa.column('email', sa.String),
        sa.column('hashed_password', sa.String),
    )
    op.bulk_insert(user_table, [
        {'id': 1, 'username': 'admin', 'email': 'admin@example.com', 'hashed_password': 'admin1234'},
    ])
    # user_role 테이블에 admin-user 매핑 추가
    user_role_table = sa.table('user_role',
        sa.column('user_id', sa.Integer),
        sa.column('role_id', sa.Integer),
    )
    op.bulk_insert(user_role_table, [
        {'user_id': 1, 'role_id': 1},
    ])


def downgrade() -> None:
    """Downgrade schema."""
    # admin user, user_role, role 데이터 삭제
    op.execute("DELETE FROM user_role WHERE user_id=1 AND role_id=1")
    op.execute("DELETE FROM users WHERE id=1 AND username='admin'")
    op.execute("DELETE FROM roles WHERE id IN (1,2)")
