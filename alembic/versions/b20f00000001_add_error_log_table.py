"""
add error_log table

Revision ID: b20f00000001
Revises: b19f019154f8
Create Date: 2025-05-23 19:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b20f00000001'
down_revision: Union[str, None] = 'b19f019154f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'error_log',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(64), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('dev_message', sa.Text(), nullable=True),
        sa.Column('url', sa.String(255), nullable=True),
        sa.Column('stack', sa.Text(), nullable=True),
        sa.Column('user', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    )

def downgrade() -> None:
    op.drop_table('error_log') 