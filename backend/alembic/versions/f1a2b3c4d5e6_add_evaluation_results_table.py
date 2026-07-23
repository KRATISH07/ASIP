"""add evaluation results table

Revision ID: f1a2b3c4d5e6
Revises: 68372c2f07de
Create Date: 2026-06-24 07:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = '68372c2f07de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'evaluation_results',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('incident_id', sa.UUID(), nullable=True),
        sa.Column('root_cause_specificity', sa.Integer(), nullable=False),
        sa.Column('action_plan_completeness', sa.Integer(), nullable=False),
        sa.Column('priority_correctness', sa.Integer(), nullable=False),
        sa.Column('factual_consistency', sa.Integer(), nullable=False),
        sa.Column('overall_quality', sa.Float(), nullable=False),
        sa.Column('flagged', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('judge_reasoning', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_evaluation_results_id'), 'evaluation_results', ['id'], unique=False)
    op.create_index(op.f('ix_evaluation_results_incident_id'), 'evaluation_results', ['incident_id'], unique=False)
    op.create_index(op.f('ix_evaluation_results_flagged'), 'evaluation_results', ['flagged'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_evaluation_results_flagged'), table_name='evaluation_results')
    op.drop_index(op.f('ix_evaluation_results_incident_id'), table_name='evaluation_results')
    op.drop_index(op.f('ix_evaluation_results_id'), table_name='evaluation_results')
    op.drop_table('evaluation_results')
