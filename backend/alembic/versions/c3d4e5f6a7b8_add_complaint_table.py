"""Add complaints table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-12 00:12:00.000000

Creates the complaints table for the Resident Complaint System.
Complaints can be filed by residents and converted to formal incidents.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types if they don't exist
    op.execute(sa.text(
        "DO $$ BEGIN "
        "  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'complaint_category_enum') THEN "
        "    CREATE TYPE complaint_category_enum AS ENUM ("
        "      'lift', 'smell', 'plumbing', 'electrical', 'noise', "
        "      'structural', 'parking', 'security', 'other'); "
        "  END IF; "
        "END $$;"
    ))
    op.execute(sa.text(
        "DO $$ BEGIN "
        "  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'complaint_priority_enum') THEN "
        "    CREATE TYPE complaint_priority_enum AS ENUM ('low', 'medium', 'high', 'urgent'); "
        "  END IF; "
        "END $$;"
    ))
    op.execute(sa.text(
        "DO $$ BEGIN "
        "  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'complaint_status_enum') THEN "
        "    CREATE TYPE complaint_status_enum AS ENUM ("
        "      'submitted', 'under_review', 'converted_to_incident', "
        "      'assigned', 'resolved', 'rejected'); "
        "  END IF; "
        "END $$;"
    ))

    # Create table using raw SQL to avoid SQLAlchemy's enum creation event hooks
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS complaints (
            id UUID PRIMARY KEY,
            resident_id UUID,
            title VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            category complaint_category_enum NOT NULL,
            priority complaint_priority_enum NOT NULL DEFAULT 'medium',
            status complaint_status_enum NOT NULL DEFAULT 'submitted',
            linked_incident_id UUID REFERENCES incidents(id) ON DELETE SET NULL,
            ai_confidence_score FLOAT,
            assigned_manager_id UUID,
            resolution_notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
    """))

    # Create indexes if they don't exist
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_complaints_id ON complaints (id);"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_complaints_resident_id ON complaints (resident_id);"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_complaints_status ON complaints (status);"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_complaints_category ON complaints (category);"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_complaints_linked_incident_id ON complaints (linked_incident_id);"))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS complaints;"))
    op.execute(sa.text("DROP TYPE IF EXISTS complaint_status_enum;"))
    op.execute(sa.text("DROP TYPE IF EXISTS complaint_priority_enum;"))
    op.execute(sa.text("DROP TYPE IF EXISTS complaint_category_enum;"))

