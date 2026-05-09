"""dedup donations by tribute_event_created_at instead of donation_request_id

Revision ID: a3f1c2d4e5f6
Revises: f4d44970a477
Create Date: 2026-05-09 21:00:00.000000

"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'a3f1c2d4e5f6'
down_revision: str | Sequence[str] | None = 'f4d44970a477'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index(
        op.f('ix_donations_tribute_donation_request_id'),
        table_name='donations',
    )
    op.create_index(
        op.f('ix_donations_tribute_donation_request_id'),
        'donations',
        ['tribute_donation_request_id'],
        unique=False,
    )

    op.add_column(
        'donations',
        sa.Column(
            'tribute_event_created_at',
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
    )

    op.execute(
        'UPDATE donations '
        'SET tribute_event_created_at = created_at '
        'WHERE tribute_event_created_at IS NULL'
    )

    op.alter_column(
        'donations',
        'tribute_event_created_at',
        existing_type=sa.TIMESTAMP(timezone=True),
        nullable=False,
    )

    op.create_index(
        op.f('ix_donations_tribute_event_created_at'),
        'donations',
        ['tribute_event_created_at'],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_donations_tribute_event_created_at'),
        table_name='donations',
    )
    op.drop_column('donations', 'tribute_event_created_at')

    op.drop_index(
        op.f('ix_donations_tribute_donation_request_id'),
        table_name='donations',
    )
    op.create_index(
        op.f('ix_donations_tribute_donation_request_id'),
        'donations',
        ['tribute_donation_request_id'],
        unique=True,
    )
