"""add prediction_accuracy to incident_memory

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-14 11:30:00.000000

Adds a dedicated prediction_accuracy column to incident_memory.
This is distinct from decision_accuracy (which scores the autonomous
decision quality). prediction_accuracy scores how accurate the
predictive_service estimates were vs actual outcomes.
"""
from alembic import op
import sqlalchemy as sa

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "incident_memory",
        sa.Column("prediction_accuracy", sa.Float(), nullable=True),
    )


def downgrade():
    op.drop_column("incident_memory", "prediction_accuracy")
