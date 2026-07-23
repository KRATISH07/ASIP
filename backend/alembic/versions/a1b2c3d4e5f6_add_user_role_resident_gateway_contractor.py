"""Add new UserRole enum values and user link columns

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-07-12 00:10:00.000000

Adds three new values to user_role_enum: resident, sensor_gateway, contractor.
Also adds optional resident_id and contractor_id link columns to the users table.

NOTE: ALTER TYPE ... ADD VALUE cannot be rolled back. The downgrade() removes the
link columns but cannot remove the added enum values from PostgreSQL.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction in older PostgreSQL.
    # Committing first, then executing outside transaction, then starting new tx.
    connection = op.get_bind()

    # Close the Alembic-managed transaction
    connection.execute(sa.text("COMMIT"))

    # Add new enum values (IF NOT EXISTS is safe for re-entrant migrations)
    connection.execute(sa.text(
        "ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'resident'"
    ))
    connection.execute(sa.text(
        "ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'sensor_gateway'"
    ))
    connection.execute(sa.text(
        "ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'contractor'"
    ))

    # Resume explicit transaction for the column additions
    connection.execute(sa.text("BEGIN"))

    # Add optional link columns to public.users
    op.add_column(
        'users',
        sa.Column('resident_id', postgresql.UUID(as_uuid=True), nullable=True),
        schema='public',
    )
    op.add_column(
        'users',
        sa.Column('contractor_id', postgresql.UUID(as_uuid=True), nullable=True),
        schema='public',
    )


def downgrade() -> None:
    # Remove the link columns (enum values cannot be removed from PostgreSQL)
    op.drop_column('users', 'contractor_id', schema='public')
    op.drop_column('users', 'resident_id', schema='public')
    # NOTE: The added enum values (resident, sensor_gateway, contractor) are NOT
    # removed because PostgreSQL does not support ALTER TYPE ... DROP VALUE.
    # Ensure no rows use these role values before applying this downgrade.
