"""add role and user_role tables

Revision ID: b7153087b068
Revises: d59e638a2862
Create Date: 2025-05-22 20:25:48.354261

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer, Text


# revision identifiers, used by Alembic.
revision: str = 'b7153087b068'
down_revision: Union[str, None] = 'd59e638a2862'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # roles 테이블 생성
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(length=50), unique=True, nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True)
    )
    # user_role 테이블 생성
    op.create_table(
        'user_role',
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('role_id', sa.Integer(), sa.ForeignKey('roles.id'), primary_key=True)
    )
    # 기본 Role 데이터 삽입
    role_table = table(
        'roles',
        column('id', Integer),
        column('name', String),
        column('description', Text)
    )
    op.bulk_insert(
        role_table,
        [
            {"id": 1, "name": "admin", "description": "관리자"},
            {"id": 2, "name": "user", "description": "일반 사용자"},
        ]
    )

def downgrade() -> None:
    op.execute("DELETE FROM roles WHERE name IN ('admin', 'user')")
    op.drop_table('user_role')
    op.drop_table('roles')
