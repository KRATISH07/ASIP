"""Check schema: list tables, indexes, and foreign keys in public schema."""
import json
import sys
import os
from sqlalchemy import create_engine, text

# Ensure backend package (app) is importable when running from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.config import settings


def main():
    url = settings.database_url.replace('+asyncpg', '+psycopg2')
    eng = create_engine(url)
    with eng.connect() as conn:
        tables = [r[0] for r in conn.execute(text("select tablename from pg_catalog.pg_tables where schemaname='public'"))]
        indexes = [r[0] for r in conn.execute(text("select indexname from pg_indexes where schemaname='public'"))]
        fks = [r for r in conn.execute(text("select conname, pg_get_constraintdef(c.oid) from pg_constraint c join pg_namespace n on c.connamespace = n.oid where n.nspname='public' and contype='f'"))]
        print(json.dumps({"tables": tables, "indexes": indexes, "fks": [dict(name=row[0], defn=row[1]) for row in fks]}, indent=2, default=str))


if __name__ == '__main__':
    main()
