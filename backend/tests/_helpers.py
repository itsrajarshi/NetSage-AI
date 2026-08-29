"""
Shared test helpers for the NetSage AI suite.
"""

import io
import os
import sys
import atexit
import tempfile
import contextlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

_SEEDED = False


def _use_isolated_db():
    """Point the DB layer at a throwaway SQLite file for the test process."""
    if os.getenv("NETSAGE_DB"):
        return
    fd, path = tempfile.mkstemp(prefix="netsage_test_", suffix=".db")
    os.close(fd)
    os.environ["NETSAGE_DB"] = path
    atexit.register(lambda: os.path.exists(path) and os.remove(path))


def ensure_seeded():
    """
    Seed the SQLite database exactly once per test process.

    Several tests assert against the seeded baseline (39 cases, 5 Responsible AI
    corrections, ACCEPTED/EDITED/REJECTED reviews). Running this from setUpClass
    lets the suite pass on a fresh clone without a manual
    `python backend/seed_data.py` step, regardless of test execution order, and
    keeps the developer's real netsage.db untouched.
    """
    global _SEEDED
    if _SEEDED:
        return
    _use_isolated_db()
    from backend.seed_data import seed
    with contextlib.redirect_stdout(io.StringIO()):
        seed()
    _SEEDED = True
