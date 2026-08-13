"""add missing conversation and message columns

Revision ID: 7a8b9c0d1e2f
Revises: 6f7a8b9c0d1e
Create Date: 2026-07-26 07:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a8b9c0d1e2f'
down_revision: Union[str, Sequence[str], None] = '6f7a8b9c0d1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Safely add columns if they do not already exist."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    conv_cols = {c['name'] for c in inspector.get_columns('conversations')}
    msg_cols = {c['name'] for c in inspector.get_columns('messages')}

    # Conversations table missing columns
    if 'is_pinned' not in conv_cols:
        op.add_column('conversations', sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'))
    if 'is_favorite' not in conv_cols:
        op.add_column('conversations', sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default='false'))
    if 'is_archived' not in conv_cols:
        op.add_column('conversations', sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'))
    if 'is_deleted' not in conv_cols:
        op.add_column('conversations', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
    if 'deleted_at' not in conv_cols:
        op.add_column('conversations', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    if 'share_token' not in conv_cols:
        op.add_column('conversations', sa.Column('share_token', sa.String(length=64), nullable=True))
        op.create_index(op.f('ix_conversations_share_token'), 'conversations', ['share_token'], unique=False)
    if 'summary' not in conv_cols:
        op.add_column('conversations', sa.Column('summary', sa.String(length=1000), nullable=True))
    if 'tags' not in conv_cols:
        op.add_column('conversations', sa.Column('tags', sa.String(length=500), nullable=True))
    if 'metadata_json' not in conv_cols:
        op.add_column('conversations', sa.Column('metadata_json', sa.String(length=2000), nullable=True))

    # Messages table missing columns
    if 'system_prompt' not in msg_cols:
        op.add_column('messages', sa.Column('system_prompt', sa.Text(), nullable=True))
    if 'attachments' not in msg_cols:
        op.add_column('messages', sa.Column('attachments', sa.Text(), nullable=True))
    if 'strategy_used' not in msg_cols:
        op.add_column('messages', sa.Column('strategy_used', sa.String(length=50), nullable=True))
    if 'routing_explanation_json' not in msg_cols:
        op.add_column('messages', sa.Column('routing_explanation_json', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove added columns from conversations and messages tables."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    conv_cols = {c['name'] for c in inspector.get_columns('conversations')}
    msg_cols = {c['name'] for c in inspector.get_columns('messages')}

    # Messages table revert
    if 'routing_explanation_json' in msg_cols:
        op.drop_column('messages', 'routing_explanation_json')
    if 'strategy_used' in msg_cols:
        op.drop_column('messages', 'strategy_used')
    if 'attachments' in msg_cols:
        op.drop_column('messages', 'attachments')
    if 'system_prompt' in msg_cols:
        op.drop_column('messages', 'system_prompt')

    # Conversations table revert
    if 'metadata_json' in conv_cols:
        op.drop_column('conversations', 'metadata_json')
    if 'tags' in conv_cols:
        op.drop_column('conversations', 'tags')
    if 'summary' in conv_cols:
        op.drop_column('conversations', 'summary')
    if 'share_token' in conv_cols:
        try:
            op.drop_index(op.f('ix_conversations_share_token'), table_name='conversations')
        except Exception:
            pass
        op.drop_column('conversations', 'share_token')
    if 'deleted_at' in conv_cols:
        op.drop_column('conversations', 'deleted_at')
    if 'is_deleted' in conv_cols:
        op.drop_column('conversations', 'is_deleted')
    if 'is_archived' in conv_cols:
        op.drop_column('conversations', 'is_archived')
    if 'is_favorite' in conv_cols:
        op.drop_column('conversations', 'is_favorite')
    if 'is_pinned' in conv_cols:
        op.drop_column('conversations', 'is_pinned')
