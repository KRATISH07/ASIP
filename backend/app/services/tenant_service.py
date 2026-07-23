import os
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.tenant import Tenant
from sqlalchemy import text
from alembic.config import Config
from alembic import command
from app.core.logging import get_logger

logger = get_logger("tenant_service")


async def provision_tenant(db: AsyncSession, name: str, slug: str) -> Tenant:
    """
    Onboard a new housing society (tenant):
    1. Creates a logically isolated PostgreSQL schema.
    2. Runs Alembic migrations dynamically to deploy all tables inside that schema.
    3. Registers the tenant in the public.tenants registry.
    """
    schema_name = f"society_{slug.replace('-', '_')}"
    logger.info("Provisioning tenant schema", slug=slug, schema_name=schema_name)

    # 1. Create schema
    await db.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
    await db.commit()

    # 2. Run migrations dynamically in-process
    original_schema = os.environ.get("ALEMBIC_SCHEMA")
    os.environ["ALEMBIC_SCHEMA"] = schema_name
    try:
        # Find absolute path to alembic.ini in the project root
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        ini_path = os.path.join(base_dir, "alembic.ini")
        
        config = Config(ini_path)
        # Execute Alembic migration upgrade script
        command.upgrade(config, "head")
        logger.info("Schema migrations executed successfully", schema=schema_name)
    except Exception as e:
        logger.error("Failed to run schema migrations for tenant", schema=schema_name, error=str(e))
        raise RuntimeError(f"Tenant database provisioning failed: {str(e)}") from e
    finally:
        if original_schema is not None:
            os.environ["ALEMBIC_SCHEMA"] = original_schema
        else:
            os.environ.pop("ALEMBIC_SCHEMA", None)

    # 3. Create Tenant record
    tenant = Tenant(name=name, slug=slug, schema_name=schema_name)
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant
