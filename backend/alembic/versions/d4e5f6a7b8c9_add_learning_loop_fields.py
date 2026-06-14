"""add learning loop fields to incident_memory

Revision ID: d4e5f6a7b8c9
Revises: c9f3e2b4a1d6
Create Date: 2026-06-14 06:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d4e5f6a7b8c9"
down_revision = "c9f3e2b4a1d6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("incident_memory", sa.Column("predicted_outage_hrs", sa.Float(), nullable=True))
    op.add_column("incident_memory", sa.Column("actual_outage_hrs",    sa.Float(), nullable=True))
    op.add_column("incident_memory", sa.Column("predicted_cost",       sa.Float(), nullable=True))
    op.add_column("incident_memory", sa.Column("actual_cost",          sa.Float(), nullable=True))
    op.add_column("incident_memory", sa.Column("decision_accuracy",    sa.Float(), nullable=True))


def downgrade():
    op.drop_column("incident_memory", "decision_accuracy")
    op.drop_column("incident_memory", "actual_cost")
    op.drop_column("incident_memory", "predicted_cost")
    op.drop_column("incident_memory", "actual_outage_hrs")
    op.drop_column("incident_memory", "predicted_outage_hrs")
