"""Load monorepo `.env` into ``os.environ`` before other app imports.

Libraries such as ``ai_agents`` validate API keys against the process environment
at import time; Pydantic Settings alone does not populate ``os.environ`` from
``.env`` for undeclared keys.
"""

from pathlib import Path

from dotenv import load_dotenv

_backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(_backend_dir.parent / ".env")
load_dotenv(_backend_dir / "local.env", override=True)
