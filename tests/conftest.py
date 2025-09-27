"""Global pytest configuration for non‑E2E tests.

Intentional separation:
- Docker-dependent fixtures and the auto e2e marker live under
  `tests/e2e/conftest.py` on purpose to keep unit/integration runs lightweight
  and free from Docker imports.
- Do not move that file here unless you also change its path-based scoping.

Shared, fast fixtures for unit/integration tests live here.
"""

from __future__ import annotations

from pathlib import Path
import os
import pytest

try:  # Optional HTTP/2 support for httpx
    import h2 as _h2  # type: ignore

    _HTTP2_AVAILABLE = True
except Exception:  # pragma: no cover
    _HTTP2_AVAILABLE = False

import httpx
from dotenv import load_dotenv


def pytest_sessionstart(session: pytest.Session) -> None:
    """Load environment variables early for local runs.

    Load order: `.env.local` then `.env` at repository root.
    """
    root = Path(__file__).resolve().parent.parent
    for name in (".env.local", ".env"):
        env_path = root / name
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)


@pytest.fixture(scope="session")
def project_id() -> str:
    """Common project id used by local emulators/tests."""
    return os.environ.get("PROJECT_ID", "test-project")


@pytest.fixture()
def http_client() -> httpx.Client:
    """Shared httpx client with sane defaults (function-scoped)."""
    with httpx.Client(http2=_HTTP2_AVAILABLE, timeout=5.0) as client:
        yield client
