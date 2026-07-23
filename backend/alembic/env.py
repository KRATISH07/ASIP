"""Alembic environment configuration for async SQLAlchemy."""
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import sys
import os

# Make app importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings
from app.db.base import Base
import app.db.models  # noqa: F401 — registers all models

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url.replace("+asyncpg", "+psycopg2"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    from sqlalchemy import text
    schema_name = os.environ.get("ALEMBIC_SCHEMA", "public")
    
    if schema_name != "public":
        # Create schema if not exists
        connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
        # Set search path to tenant schema
        connection.execute(text(f'SET search_path TO "{schema_name}"'))
        
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        version_table_schema=schema_name
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    async_url = settings.database_url
    connectable = async_engine_from_config(
        {"sqlalchemy.url": async_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
