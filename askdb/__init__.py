"""askdb — natural-language analytics over the company warehouse."""

import os
from pathlib import Path

__version__ = "2.3.0"


def _load_dotenv() -> None:
    """Read KEY=value lines from the repo's .env, without overriding the environment."""
    env = Path(__file__).resolve().parent.parent / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() and not key.lstrip().startswith("#"):
                os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()
