"""
Add module_env_vars table for per-module environment variables
"""

# revision identifiers, used by Alembic.
revision = '20240628_add_module_env_vars'
down_revision = 'b247dbb084dc'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'module_env_vars',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('module_id', sa.Integer, sa.ForeignKey('modules.id'), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', sa.String(512), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

def downgrade():
    op.drop_table('module_env_vars') 