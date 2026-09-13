"""add avatar url, contract document url, and proposal skills

Revision ID: b2c4d6e8f0a1
Revises: 6025eb4a8ae0
Create Date: 2026-09-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c4d6e8f0a1'
down_revision: Union[str, Sequence[str], None] = '6025eb4a8ae0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('freelancer_profiles', sa.Column('avatar_url', sa.String(length=255), nullable=True))
    op.add_column('contracts', sa.Column('document_url', sa.String(length=255), nullable=True))
    op.create_table('proposal_skills',
    sa.Column('proposal_id', sa.UUID(), nullable=False),
    sa.Column('skill_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['proposal_id'], ['proposals.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('proposal_id', 'skill_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('proposal_skills')
    op.drop_column('contracts', 'document_url')
    op.drop_column('freelancer_profiles', 'avatar_url')
