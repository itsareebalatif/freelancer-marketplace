"""add full_name to users and hash refresh tokens

Revision ID: a1b2c3d4e5f6
Revises: d0e5e771822d
Create Date: 2026-09-10 13:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'd0e5e771822d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('full_name', sa.String(length=255), nullable=True))

    op.drop_index(op.f('ix_refresh_tokens_token'), table_name='refresh_tokens')
    op.alter_column('refresh_tokens', 'token', new_column_name='token_hash', type_=sa.String(length=128))
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_refresh_tokens_token_hash'), table_name='refresh_tokens')
    op.alter_column('refresh_tokens', 'token_hash', new_column_name='token', type_=sa.String(length=512))
    op.create_index(op.f('ix_refresh_tokens_token'), 'refresh_tokens', ['token'], unique=True)

    op.drop_column('users', 'full_name')
