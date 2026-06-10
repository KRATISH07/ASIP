#!/usr/bin/env python3
"""Validate Memory Layer against real infrastructure (Postgres + Chroma).

This script performs the following checks and actions:
- Verifies Postgres and Chroma connectivity
- Applies Alembic migrations (unless skipped)
- Seeds the database (unless skipped)
- Stores an Incident A into memory (Postgres + Chroma)
- Verifies DB record and Chroma indexing
- Runs Incident B through Infrastructure, Contractor, Supervisor agents
  (using mock LLMs by default) and verifies memory injection

Usage:
  python backend/scripts/validate_memory_real_infra.py [--use-real-llm] [--skip-migrate] [--skip-seed]

Note: run from repository root. This script uses the project's Python
environment. It does not modify application logic; it only performs
validation and uses dependency injection where necessary.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"

# Make sure backend is importable
sys.path.insert(0, str(BACKEND))


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


async def check_postgres(database_url: str, timeout: int = 5) -> (bool, str):
    """Attempt to connect to Postgres using psycopg2.

    Returns (ok, message).
    """
    try:
        try:
            import psycopg2
        except Exception as exc:  # pragma: no cover - env dependent
            return False, f"psycopg2 not available: {exc}"
        # Prefer using the application's SQLAlchemy engine (same approach as app.db.session)
        try:
            # Import the application's DB session to reuse its engine configuration
            from app.db import session as db_session
            # Async engine exposes a .sync_engine for synchronous operations
            engine_obj = getattr(db_session, "engine", None)
            sync_engine = getattr(engine_obj, "sync_engine", engine_obj)
            if sync_engine is not None:
                from sqlalchemy import text

                with sync_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                return True, "Postgres reachable (via SQLAlchemy engine)"
        except Exception:
            # if any error occurs, fall back to constructing connection via psycopg2
            pass

        # Parse SQLAlchemy-style URL (handles +asyncpg, +psycopg2, etc.) and use psycopg2
        try:
            from sqlalchemy.engine.url import make_url

            url_obj = make_url(database_url)
            conn_kwargs = {}
            if url_obj.database:
                conn_kwargs["dbname"] = url_obj.database
            if url_obj.username:
                conn_kwargs["user"] = url_obj.username
            if url_obj.password:
                conn_kwargs["password"] = url_obj.password
            if url_obj.host:
                conn_kwargs["host"] = url_obj.host
            if url_obj.port:
                conn_kwargs["port"] = url_obj.port
            conn_kwargs["connect_timeout"] = timeout

            conn = psycopg2.connect(**conn_kwargs)
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
            cur.close()
            conn.close()
            return True, "Postgres reachable"
        except Exception:
            # Fallback: try normalizing by removing SQLAlchemy driver hints like +asyncpg or +psycopg2
            simple_url = database_url.replace("+asyncpg", "").replace("+psycopg2", "")
            conn = psycopg2.connect(simple_url, connect_timeout=timeout)
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
            cur.close()
            conn.close()
            return True, "Postgres reachable (fallback)"
    except Exception as exc:  # pragma: no cover - env dependent
        return False, str(exc)


async def check_chroma(host: str, port: int, timeout: int = 5) -> (bool, str):
    try:
        import httpx
    except Exception:
        # fallback to socket
        import socket

        s = socket.socket()
        s.settimeout(timeout)
        try:
            s.connect((host, int(port)))
            s.close()
            return True, "Chroma port open"
        except Exception as exc:
            return False, str(exc)

    try:
        url = f"http://{host}:{port}/"
        r = httpx.get(url, timeout=timeout)
        return True, f"HTTP {r.status_code}"
    except Exception as exc:
        return False, str(exc)


def run_alembic_upgrade(backend_dir: Path, db_url: str) -> (bool, str):
    # Run Alembic in a separate subprocess to avoid nested event loop issues.
    cfg_path = backend_dir / "alembic.ini"
    if not cfg_path.exists():
        return False, f"alembic.ini not found at {cfg_path}"

    # Normalize URL for alembic (use psycopg2 driver for sync operations)
    sync_url = db_url.replace("+asyncpg", "+psycopg2")

    # Build a small Python snippet to run alembic upgrade in a fresh interpreter
    # Use json.dumps to safely quote the URL
    python_snippet = (
        "from alembic.config import Config\n"
        "from alembic import command\n"
        "import sys\n"
        "cfg = Config('alembic.ini')\n"
        "cfg.set_main_option('script_location', 'alembic')\n"
        f"cfg.set_main_option('sqlalchemy.url', {json.dumps(sync_url)})\n"
        "command.upgrade(cfg, 'head')\n"
    )

    try:
        # Ensure subprocess picks up a sync URL via environment so alembic/env.py
        # (which imports app.config.Settings) will see the sync URL instead of asyncpg
        env_vars = os.environ.copy()
        # env should expose the original (possibly asyncpg) DB URL so alembic/env.py
        # can create an async engine when needed. env.py itself will set a sync
        # ``sqlalchemy.url`` for parts that need a sync driver.
        env_vars["DATABASE_URL"] = db_url
        env_vars["database_url"] = db_url
        proc = subprocess.run(
            [sys.executable, "-c", python_snippet],
            cwd=str(backend_dir),
            capture_output=True,
            text=True,
            env=env_vars,
            timeout=300,
        )
    except Exception as exc:
        return False, f"Failed to run alembic subprocess: {exc}"

    out = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if proc.returncode != 0:
        return False, out
    return True, out


def run_seed_script(backend_dir: Path) -> (bool, str):
    """Run the seeds script as a subprocess using current Python."""
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "seeds.seed"], cwd=str(backend_dir), capture_output=True, text=True
        )
        if proc.returncode != 0:
            return False, proc.stdout + "\n" + proc.stderr
        return True, proc.stdout
    except Exception as exc:
        return False, str(exc)


class FakeEmbeddings:
    """Simple deterministic embedding fallback used for validation when
    real embedding models (OpenAI/Gemini) are unavailable.
    """

    def __init__(self, dim: int = 8):
        self.dim = dim

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        out = []
        for t in texts:
            l = len(t or "")
            v = [float((l % 97) + i) / 100.0 for i in range(self.dim)]
            out.append(v)
        return out

    def embed_query(self, text: str) -> List[float]:
        l = len(text or "")
        return [float((l % 97) + i) / 100.0 for i in range(self.dim)]


class RecordingLLM:
    """A mock LLM that records payloads and returns JSON-compatible strings.

    `behavior` may be a callable(payload)->dict or a constant dict.
    """

    def __init__(self, behavior: Callable[[Dict[str, Any]], Any], recorder: List[Dict[str, Any]]):
        self.behavior = behavior
        self.recorder = recorder

    def __or__(self, other):
        async def run(payload: Dict[str, Any]):
            try:
                self.recorder.append(payload)
            except Exception:
                pass
            try:
                if callable(self.behavior):
                    res = self.behavior(payload)
                else:
                    res = self.behavior
                if isinstance(res, str):
                    return res
                return json.dumps(res)
            except Exception:
                return json.dumps({"error": "llm-behavior-failed"})

        return run


async def main(argv: Optional[List[str]] = None):
    p = argparse.ArgumentParser()
    p.add_argument("--use-real-llm", action="store_true", help="Allow calling real LLMs (OpenAI/Gemini) if configured")
    p.add_argument("--skip-migrate", action="store_true", help="Skip Alembic migrations")
    p.add_argument("--skip-seed", action="store_true", help="Skip running seeds script")
    args = p.parse_args(argv)

    report: Dict[str, str] = {}

    # Import settings
    try:
        from app.config import settings
    except Exception as exc:
        eprint("Failed to import app.config.settings:", exc)
        raise

    db_url = settings.database_url
    chroma_host = settings.chroma_host
    chroma_port = settings.chroma_port

    print("\n=== Infrastructure Validation: Starting checks ===\n")

    # 1) Connectivity checks
    ok_pg, msg_pg = await check_postgres(db_url)
    report["PostgreSQL"] = "WORKING" if ok_pg else f"FAILED: {msg_pg}"
    print("PostgreSQL:", report["PostgreSQL"])

    ok_ch, msg_ch = await check_chroma(chroma_host, chroma_port)
    report["ChromaDB"] = "WORKING" if ok_ch else f"FAILED: {msg_ch}"
    print("ChromaDB:", report["ChromaDB"])

    if not ok_pg or not ok_ch:
        print("\nOne or more infrastructure services are unreachable. Aborting validation.")
        print("Next Recommended Action: Start Postgres and Chroma (docker compose) and retry.")
        print("Example: docker compose up -d postgres chromadb")
        print("\nDetailed status:\n", json.dumps(report, indent=2))
        return 1

    # 2) Apply Alembic migrations
    if args.skip_migrate:
        print("Skipping migrations (--skip-migrate)")
        report["Migration Status"] = "SKIPPED"
    else:
        ok_mig, msg_mig = run_alembic_upgrade(BACKEND, db_url)
        # Always capture migration logs in the report
        report["Migration Logs"] = msg_mig
        if ok_mig:
            report["Migration Status"] = "WORKING"
            print("Migration Status: WORKING")
            print("Migration logs:\n", msg_mig)
        else:
            report["Migration Status"] = f"FAILED: {msg_mig}"
            print("Migration Status: FAILED")
            print("Migration logs:\n", msg_mig)
            print("Next Recommended Action: ensure alembic is installed and DATABASE_URL points to Postgres.")
            return 2

    # 3) Seed DB (optional)
    if args.skip_seed:
        print("Skipping seed (--skip-seed)")
        report["Seed Status"] = "SKIPPED"
    else:
        ok_seed, msg_seed = run_seed_script(BACKEND)
        report["Seed Status"] = "WORKING" if ok_seed else f"FAILED: {msg_seed}"
        print("Seed Status:", report["Seed Status"])
        if not ok_seed:
            print("Seeding failed; check output above. You can try running:\n  python -m seeds.seed\nfrom backend directory.")
            return 3

    # 4) Memory store & retrieval
    try:
        import importlib
        memory_service = importlib.import_module("app.services.memory_service")
        # Monkeypatch embedding model to a deterministic lightweight fallback
        import app.agents.llm as llm_mod
        llm_mod.get_embedding_model = lambda: FakeEmbeddings(dim=8)
    except Exception as exc:
        eprint("Failed to prepare memory_service or embedding shim:", exc)
        traceback.print_exc()
        return 4

    incident_a = {
        "incident_id": str(__import__("uuid").uuid4()),
        "incident_event": {"type": "water_pressure_drop", "severity": "critical"},
        "impact": {"estimated_residents": 42},
        "contractor_recommendation": {"contractor_name": "AquaFix Pro"},
        "final_report": {"incident_summary": "Replaced pump and restored flow", "root_cause": "Pump failure", "estimated_resolution_hrs": 4.0},
    }

    print("\nStoring Incident A into memory (Postgres + Chroma)...")
    try:
        mem = await memory_service.store_incident_memory(incident_a)
        report["Memory Storage"] = "WORKING"
        print("Stored IncidentMemory with uuid:", getattr(mem, "incident_uuid", None))
    except Exception as exc:
        report["Memory Storage"] = f"FAILED: {exc}"
        eprint("Failed to store incident memory:", exc)
        traceback.print_exc()
        return 5

    # verify record in Postgres
    try:
        # Prefer using the application's SQLAlchemy sync engine for verification
        try:
            from app.db import session as db_session
            from sqlalchemy import text

            engine_obj = getattr(db_session, "engine", None)
            sync_engine = getattr(engine_obj, "sync_engine", engine_obj)
            if sync_engine is not None:
                with sync_engine.connect() as conn:
                    res = conn.execute(
                        text(
                            "SELECT incident_uuid, incident_type, resolution_summary FROM incident_memory WHERE incident_uuid::text = :id"
                        ),
                        {"id": str(getattr(mem, "incident_uuid"))},
                    )
                    row = res.fetchone()
                if row:
                    report["PostgreSQL:IncidentRecord"] = "WORKING"
                    print("Postgres record found for Incident A")
                else:
                    report["PostgreSQL:IncidentRecord"] = "FAILED"
                    print("Postgres record NOT found for Incident A")
            else:
                raise RuntimeError("No sync engine available")
        except Exception:
            # Fallback to psycopg2 using SQLAlchemy URL parsing
            import psycopg2
            from sqlalchemy.engine.url import make_url

            url_obj = make_url(db_url)
            conn_kwargs = {}
            if url_obj.database:
                conn_kwargs["dbname"] = url_obj.database
            if url_obj.username:
                conn_kwargs["user"] = url_obj.username
            if url_obj.password:
                conn_kwargs["password"] = url_obj.password
            if url_obj.host:
                conn_kwargs["host"] = url_obj.host
            if url_obj.port:
                conn_kwargs["port"] = url_obj.port
            conn_kwargs["connect_timeout"] = 5

            conn = psycopg2.connect(**conn_kwargs)
            cur = conn.cursor()
            cur.execute(
                "SELECT incident_uuid, incident_type, resolution_summary FROM incident_memory WHERE incident_uuid::text = %s",
                (str(getattr(mem, "incident_uuid")),),
            )
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row:
                report["PostgreSQL:IncidentRecord"] = "WORKING"
                print("Postgres record found for Incident A (psycopg2)")
            else:
                report["PostgreSQL:IncidentRecord"] = "FAILED"
                print("Postgres record NOT found for Incident A (psycopg2)")
    except Exception as exc:
        report["PostgreSQL:IncidentRecord"] = f"FAILED: {exc}"
        eprint("Error verifying Postgres record:", exc)

    # verify retrieval from Chroma
    try:
        retrieved = await memory_service.retrieve_similar_incidents({"incident_type": "water_pressure_drop"}, k=3)
        if retrieved and any((r.get("resolution_summary") or "") for r in retrieved):
            report["Memory Retrieval"] = "WORKING"
            print("Chroma retrieval returned items:", len(retrieved))
        else:
            report["Memory Retrieval"] = "FAILED"
            print("Chroma retrieval returned no usable items")
    except Exception as exc:
        report["Memory Retrieval"] = f"FAILED: {exc}"
        eprint("Error during Chroma retrieval:", exc)

    # 5) Run agents with mock LLMs (unless user asked for real LLMs)
    infra_inputs: List[Dict[str, Any]] = []
    contractor_inputs: List[Dict[str, Any]] = []
    supervisor_inputs: List[Dict[str, Any]] = []

    # Define per-agent behaviors that reference the incoming payload
    def infra_behavior(payload):
        # simply echo that retrieved context exists
        ctx = payload.get("context") or ""
        return {"probable_cause": "Pump failure", "recommended_action": "Replace pump", "confidence": 0.9, "retrieved_context": ctx}

    def contractor_behavior(payload):
        hist = payload.get("historical_incidents") or ""
        return {"contractor_name": "AquaFix Pro", "estimated_cost": 8000.0, "estimated_time_hrs": 2.0, "selection_reasoning": f"Based on history: {hist[:80]}"}

    def supervisor_behavior(payload):
        history = payload.get("history") or ""
        return {"incident_summary": f"Supervisor used history -> {history.splitlines()[0] if history else 'none'}", "root_cause": "Pump failure", "impact_summary": "42 residents affected", "action_plan": "1. Replace pump", "estimated_resolution_hrs": 4.0, "priority": "critical"}

    # Import agents modules and patch get_llm at module-level so agents use our RecordingLLM
    import importlib
    infra_mod = importlib.import_module("app.agents.infrastructure")
    contractor_mod = importlib.import_module("app.agents.contractor")
    supervisor_mod = importlib.import_module("app.agents.supervisor")

    if args.use_real_llm:
        print("--use-real-llm specified: agents will call real LLMs if configured via settings.")
    else:
        infra_mod.get_llm = lambda temperature=0.1: RecordingLLM(infra_behavior, infra_inputs)
        contractor_mod.get_llm = lambda temperature=0.1: RecordingLLM(contractor_behavior, contractor_inputs)
        supervisor_mod.get_llm = lambda temperature=0.1: RecordingLLM(supervisor_behavior, supervisor_inputs)

    # Incident B: similar issue
    incident_b = {
        "incident_id": str(__import__("uuid").uuid4()),
        "sensor_data": {"tower_id": "tower-b", "sensor_type": "water_pressure", "value": 0.25},
        "incident_event": {"type": "water_pressure_drop", "severity": "critical"},
    }

    # Run infrastructure agent
    try:
        infra_state = await infra_mod.infrastructure_agent(dict(incident_b))
        # Check that our RecordingLLM recorded payload and that context included the incident summary
        infra_ok = any("Replaced pump" in (p.get("context") or "") or "Replaced pump" in str(p) for p in infra_inputs)
        report["Infrastructure Memory"] = "WORKING" if infra_ok else "FAILED"
        print("Infrastructure agent memory injection:", report["Infrastructure Memory"])
    except Exception as exc:
        report["Infrastructure Memory"] = f"FAILED: {exc}"
        eprint("Infrastructure agent run failed:", exc)

    # Run contractor agent (use infra_state for continuity)
    try:
        contractor_state = await contractor_mod.contractor_agent(dict(infra_state))
        contractor_ok = any("Replaced pump" in (p.get("historical_incidents") or "") or "Replaced pump" in str(p) for p in contractor_inputs)
        report["Contractor Memory"] = "WORKING" if contractor_ok else "FAILED"
        print("Contractor agent memory injection:", report["Contractor Memory"])
    except Exception as exc:
        report["Contractor Memory"] = f"FAILED: {exc}"
        eprint("Contractor agent run failed:", exc)

    # Run supervisor agent
    try:
        sup_state = await supervisor_mod.supervisor_agent(dict(contractor_state))
        sup_ok = any("Replaced pump" in (p.get("history") or "") or "Replaced pump" in str(p) for p in supervisor_inputs)
        # Also check final_report references historical incident text if possible
        final_ref = False
        fr = sup_state.get("final_report") or {}
        # final_report may be dict or JSON-string; normalize
        if isinstance(fr, str):
            final_ref = "Replaced pump" in fr
        elif isinstance(fr, dict):
            final_ref = any("Replaced pump" in str(v) for v in fr.values())

        report["Supervisor Memory"] = "WORKING" if (sup_ok or final_ref) else "FAILED"
        print("Supervisor agent memory injection:", report["Supervisor Memory"])
    except Exception as exc:
        report["Supervisor Memory"] = f"FAILED: {exc}"
        eprint("Supervisor agent run failed:", exc)

    # Overall assessment
    overall = "PASS" if all(v.startswith("WORKING") for v in [report.get("PostgreSQL",""), report.get("ChromaDB",""), report.get("Memory Storage",""), report.get("Memory Retrieval",""), report.get("Infrastructure Memory",""), report.get("Contractor Memory",""), report.get("Supervisor Memory",
                                                                                                                      "")]) else "FAIL"

    print("\n=== Infrastructure Validation Report ===\n")
    for k in ["PostgreSQL", "ChromaDB", "Migration Status", "Seed Status", "Memory Storage", "PostgreSQL:IncidentRecord", "Memory Retrieval", "Infrastructure Memory", "Contractor Memory", "Supervisor Memory"]:
        if k in report:
            print(f"{k}: {report[k]}")
    print(f"\nOverall: {overall}\n")

    # Next recommended action
    if overall == "PASS":
        print("Next Recommended Action: Proceed to run full integration tests or enable real LLMs for further validation.")
    else:
        print("Next Recommended Action: Inspect failures above. Common fixes:\n- Ensure Postgres is healthy and migrations applied\n- Ensure Chroma is reachable and persistent\n- Re-run with --skip-seed to seed manually if seeding failed\n- Enable logs for detailed error traces")

    return 0 if overall == "PASS" else 5


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
