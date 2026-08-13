"""create provider_configs table

Revision ID: 6f7a8b9c0d1e
Revises: 5d9fcee317fe
Create Date: 2026-07-25 21:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f7a8b9c0d1e'
down_revision: Union[str, Sequence[str], None] = '5d9fcee317fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply provider_configs table schema changes."""
    op.create_table(
        'provider_configs',
        sa.Column('provider_id', sa.String(length=50), nullable=False),
        sa.Column('provider_name', sa.String(length=100), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('api_key_encrypted', sa.String(length=500), nullable=True),
        sa.Column('base_url', sa.String(length=300), nullable=True),
        sa.Column('organization_id', sa.String(length=100), nullable=True),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('rate_limit_rpm', sa.Integer(), nullable=False, server_default='600'),
        sa.Column('rate_limit_tpm', sa.Integer(), nullable=False, server_default='100000'),
        sa.Column('default_model', sa.String(length=100), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('cost_multiplier', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('primary_provider_id', sa.String(length=50), nullable=True),
        sa.Column('secondary_provider_id', sa.String(length=50), nullable=True),
        sa.Column('auto_failover', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('supports_streaming', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('supports_vision', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('supports_audio', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('supports_function_calling', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('supports_embeddings', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('supports_image_generation', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('supports_moderation', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='unconfigured'),
        sa.Column('last_latency_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_health_check', sa.DateTime(), nullable=True),
        sa.Column('last_failure', sa.DateTime(), nullable=True),
        sa.Column('failure_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('provider_id')
    )


def downgrade() -> None:
    """Revert provider_configs table."""
    op.drop_table('provider_configs')
