"""add incident_memory table

Revision ID: ae3f2b8b1c3d
Revises: 
Create Date: 2026-06-09 23:50:00.000000
"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

# revision identifiers, used by Alembic.
revision = "ae3f2b8b1c3d"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "incident_memory",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("incident_uuid", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("incident_type", sa.String(), nullable=True),
        sa.Column("root_cause", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(), nullable=True),
        sa.Column("affected_residents", sa.Integer(), nullable=True),
        sa.Column("contractor_used", sa.String(), nullable=True),
        sa.Column("repair_duration_hours", sa.Float(), nullable=True),
        sa.Column("resolution_summary", sa.Text(), nullable=True),
    )
    op.create_index("ix_incident_memory_incident_uuid", "incident_memory", ["incident_uuid"])
    op.create_index("ix_incident_memory_incident_type", "incident_memory", ["incident_type"])
    op.create_index("ix_incident_memory_severity", "incident_memory", ["severity"])


def downgrade():
    op.drop_index("ix_incident_memory_severity", table_name="incident_memory")
    op.drop_index("ix_incident_memory_incident_type", table_name="incident_memory")
    op.drop_index("ix_incident_memory_incident_uuid", table_name="incident_memory")
    op.drop_table("incident_memory")
