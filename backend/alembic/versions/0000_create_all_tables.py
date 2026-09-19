"""Create all tables — clean initial migration for fresh databases (e.g. Neon)

Revision ID: 0000_create_all_tables
Revises:
Create Date: 2026-09-19
"""
import asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import op
from app.db.base import Base
import app.db.models  # noqa: F401 — registers all models on Base.metadata
import os

# revision identifiers, used by Alembic.
revision = "0000_create_all"
down_revision = None
branch_labels = "create_all"
depends_on = None


def upgrade():
    # Use SQLAlchemy metadata create_all via a raw connection
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade():
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
