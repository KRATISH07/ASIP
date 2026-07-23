"""Add sensor_event_buffer table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-12 00:11:00.000000

Creates the sensor_event_buffer table used by the Store-and-Forward feature.
Edge gateways upload buffered events here when network connectivity is restored.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the sync_status enum type if it doesn't exist
    op.execute(sa.text(
        "DO $$ BEGIN "
        "  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sync_status_enum') THEN "
        "    CREATE TYPE sync_status_enum AS ENUM ('pending', 'synced', 'failed'); "
        "  END IF; "
        "END $$;"
    ))

    # Create table using raw SQL to avoid SQLAlchemy's enum creation event hooks
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS sensor_event_buffer (
            id UUID PRIMARY KEY,
            sensor_id VARCHAR(100) NOT NULL,
            idempotency_key VARCHAR(255) NOT NULL UNIQUE,
            payload JSONB NOT NULL,
            event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            received_at TIMESTAMP WITH TIME ZONE NOT NULL,
            sync_status sync_status_enum NOT NULL DEFAULT 'pending',
            retry_count INTEGER NOT NULL DEFAULT 0,
            last_attempt_at TIMESTAMP WITH TIME ZONE,
            error_message TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
    """))

    # Create indexes if they don't exist
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_sensor_event_buffer_id ON sensor_event_buffer (id);"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_sensor_event_buffer_sync_status ON sensor_event_buffer (sync_status);"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_sensor_event_buffer_sensor_id ON sensor_event_buffer (sensor_id);"))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS sensor_event_buffer;"))
    op.execute(sa.text("DROP TYPE IF EXISTS sync_status_enum;"))

