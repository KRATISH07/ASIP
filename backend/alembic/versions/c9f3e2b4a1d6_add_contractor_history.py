"""add contractor_history table

Revision ID: c9f3e2b4a1d6
Revises: ae3f2b8b1c3d
Create Date: 2026-06-10 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

# revision identifiers, used by Alembic.
revision = "c9f3e2b4a1d6"
down_revision = "ae3f2b8b1c3d"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "contractor_history",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("contractor_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("incident_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("incident_type", sa.String(), nullable=True),
        sa.Column("repair_duration_hours", sa.Float(), nullable=True),
        sa.Column("repair_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("resolution_success", sa.Boolean(), nullable=True),
        sa.Column("resident_feedback_score", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["contractor_id"], ["contractors.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_contractor_history_contractor_id", "contractor_history", ["contractor_id"])
    op.create_index("ix_contractor_history_incident_id", "contractor_history", ["incident_id"])
    op.create_index("ix_contractor_history_incident_type", "contractor_history", ["incident_type"])


def downgrade():
    op.drop_index("ix_contractor_history_incident_type", table_name="contractor_history")
    op.drop_index("ix_contractor_history_incident_id", table_name="contractor_history")
    op.drop_index("ix_contractor_history_contractor_id", table_name="contractor_history")
    op.drop_table("contractor_history")
