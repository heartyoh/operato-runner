"""Add database-compatible timestamp defaults

Revision ID: db_compatible_timestamps
Revises: 5903ddc03e87
Create Date: 2025-09-10 00:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'db_compatible_timestamps'
down_revision: Union[str, None] = '5903ddc03e87'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def get_timestamp_default():
    """데이터베이스별 현재시간 기본값 반환"""
    bind = op.get_bind()
    dialect = bind.dialect.name
    
    if dialect == 'postgresql':
        return sa.text('NOW()')
    elif dialect == 'mysql':
        return sa.text('NOW()')
    elif dialect == 'sqlite':
        return sa.text("(datetime('now'))")
    else:
        # 기본값
        return sa.text('NOW()')

def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    dialect = bind.dialect.name
    
    if dialect == 'sqlite':
        # SQLite는 기존 마이그레이션이 이미 올바름
        pass
    elif dialect in ['postgresql', 'mysql']:
        # PostgreSQL/MySQL용 timestamp 기본값 수정
        timestamp_default = get_timestamp_default()
        
        # 기존 테이블들의 timestamp 컬럼 수정
        tables_with_created_at = [
            'module_validation_logs', 'users', 'audit_logs', 'modules', 
            'module_env_vars', 'versions', 'temp_files'
        ]
        
        for table in tables_with_created_at:
            try:
                op.alter_column(table, 'created_at', 
                    existing_type=sa.DateTime(),
                    server_default=timestamp_default
                )
            except Exception:
                # 테이블이 없거나 컬럼이 없으면 무시
                pass
        
        # updated_at 컬럼이 있는 테이블들
        tables_with_updated_at = ['modules', 'module_env_vars']
        
        for table in tables_with_updated_at:
            try:
                op.alter_column(table, 'updated_at',
                    existing_type=sa.DateTime(), 
                    server_default=timestamp_default
                )
            except Exception:
                pass

def downgrade() -> None:
    """Downgrade schema."""
    # 기본값 변경은 되돌리기 어려우므로 pass
    pass