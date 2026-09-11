"""add advanced job fields (budget_type, experience_level, duration, location_type, category, deadline)

Revision ID: 6025eb4a8ae0
Revises: a1b2c3d4e5f6
Create Date: 2026-09-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6025eb4a8ae0'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'jobs',
        sa.Column(
            'budget_type',
            sa.Enum('FIXED', 'HOURLY', name='budgettype', native_enum=False),
            nullable=False,
            server_default='FIXED',
        ),
    )
    op.add_column(
        'jobs',
        sa.Column(
            'experience_level',
            sa.Enum('ENTRY', 'INTERMEDIATE', 'EXPERT', name='experiencelevel', native_enum=False),
            nullable=False,
            server_default='INTERMEDIATE',
        ),
    )
    op.add_column(
        'jobs',
        sa.Column(
            'duration',
            sa.Enum(
                'LESS_THAN_1_MONTH', 'ONE_TO_3_MONTHS', 'THREE_TO_6_MONTHS', 'MORE_THAN_6_MONTHS',
                name='jobduration', native_enum=False,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        'jobs',
        sa.Column(
            'location_type',
            sa.Enum('REMOTE', 'ONSITE', 'HYBRID', name='locationtype', native_enum=False),
            nullable=False,
            server_default='REMOTE',
        ),
    )
    op.add_column('jobs', sa.Column('category', sa.String(length=100), nullable=True))
    op.add_column('jobs', sa.Column('deadline', sa.DateTime(timezone=True), nullable=True))

    op.create_index(op.f('ix_jobs_location_type'), 'jobs', ['location_type'], unique=False)
    op.create_index(op.f('ix_jobs_category'), 'jobs', ['category'], unique=False)

    op.alter_column('jobs', 'budget_type', server_default=None)
    op.alter_column('jobs', 'experience_level', server_default=None)
    op.alter_column('jobs', 'location_type', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_jobs_category'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_location_type'), table_name='jobs')

    op.drop_column('jobs', 'deadline')
    op.drop_column('jobs', 'category')
    op.drop_column('jobs', 'location_type')
    op.drop_column('jobs', 'duration')
    op.drop_column('jobs', 'experience_level')
    op.drop_column('jobs', 'budget_type')
