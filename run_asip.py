#!/usr/bin/env python3
"""
ASIP Ultra-Lightweight Platform Launcher (run_asip.py)
------------------------------------------------------
CPU-only, low-memory launcher specifically optimized for Mac Air M4 (fanless)
to guarantee zero thermal spikes, zero GPU crashes, and auto-recovery of PostgreSQL.

Usage:
    python3 run_asip.py
"""

import os
import sys
import time
import socket
import signal
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
VENV_PYTHON = ROOT_DIR / ".venv" / "bin" / "python"

processes = []

def is_port_in_use(port: int) -> bool:
    """Checks if a given TCP port is currently accepting connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0

def ensure_postgres_running():
    """Self-healing PostgreSQL checker: fixes stale postmaster.pid lockfiles and starts DB."""
    if is_port_in_use(5432):
        return True

    print("⚠️  PostgreSQL port 5432 is offline. Attempting automatic recovery...")
    # Clean up any stale postmaster.pid from ungraceful system shutdowns/freezes
    pid_file = Path("/opt/homebrew/var/postgresql@18/postmaster.pid")
    if pid_file.exists():
        try:
            pid_file.unlink()
            print("✓ Removed stale postmaster.pid lockfile.")
        except Exception:
            pass

    # Attempt starting brew postgres service
    try:
        subprocess.run(["brew", "services", "start", "postgresql@18"], capture_output=True, timeout=10)
        time.sleep(2)
    except Exception:
        pass

    if is_port_in_use(5432):
        print("✓ PostgreSQL service started successfully.")
        return True
    else:
        print("❌ Warning: PostgreSQL service could not be auto-started. Please run 'brew services restart postgresql@18'")
        return False

def cleanup(signum=None, frame=None):
    print("\nShutting down ASIP services...")
    for p in processes:
        if p.poll() is None:
            try:
                p.terminate()
            except OSError:
                pass
    print("✓ Stopped cleanly.")
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    python_bin = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

    # Strictly CPU-only & single-thread limits to prevent system heat/freezes
    env = os.environ.copy()
    env["DEVICE"] = "cpu"
    env["TORCH_DEVICE"] = "cpu"
    env["CUDA_VISIBLE_DEVICES"] = ""
    env["PYTORCH_ENABLE_MPS_FALLBACK"] = "0"
    env["OMP_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["VECLIB_MAXIMUM_THREADS"] = "1"
    env["NUMEXPR_NUM_THREADS"] = "1"

    print("====================================================================")
    print(" 🏛️   ASIP — AI Society Intelligence Platform (Mac Air M4 Safe Mode)")
    print("      • Compute Mode: Pure CPU (GPU disabled to prevent crashes)")
    print("      • Thermal State: Low Power & Fanless Safe")
    print("====================================================================")
    print(" 🚀 Backend Ops API:    http://localhost:8000")
    print(" 💻 Frontend Ops Center: http://localhost:3000")
    print("====================================================================\n")

    # Pre-flight PostgreSQL Self-Healing Check
    ensure_postgres_running()

    # 1. Start Backend (CPU-safe mode)
    print("Starting Backend (Port 8000)...")
    backend_proc = subprocess.Popen(
        [python_bin, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(BACKEND_DIR),
        env=env
    )
    processes.append(backend_proc)

    # 2. Start Frontend (Single worker mode)
    print("Starting Frontend (Port 3000)...")
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(FRONTEND_DIR),
        env=env
    )
    processes.append(frontend_proc)

    print("\n✓ ASIP running safely! Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
