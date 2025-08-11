"""Add temp_files table for multimedia support

Revision ID: add_temp_files
Revises: d75cf45ba241
Create Date: 2025-08-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_temp_files'
down_revision = 'd75cf45ba241'
branch_labels = None
depends_on = None

def upgrade():
    # 임시 파일 테이블 생성
    op.create_table('temp_files',
        sa.Column('id', sa.String(100), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('content_type', sa.String(100), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('file_type', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_temp_files_id'), 'temp_files', ['id'], unique=False)

def downgrade():
    # 임시 파일 테이블 삭제
    op.drop_index(op.f('ix_temp_files_id'), table_name='temp_files')
    op.drop_table('temp_files')