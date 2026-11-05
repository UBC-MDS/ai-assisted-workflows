"""Structured request tracing.

Append-only JSONL, one object per request. Set ASKDB_TRACE_PATH to write elsewhere.
"""

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TRACE_PATH = Path(os.environ.get(
    "ASKDB_TRACE_PATH", Path(__file__).resolve().parent.parent / "logs" / "traces.jsonl"))


@dataclass
class Trace:
    """One askdb request, start to finish."""

    question: str
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    ts: str = ""
    release: str = ""
    source: str = "adhoc"                 # adhoc | scheduled_report
    report_id: str | None = None          # set for scheduled reports
    model: str = ""
    schema_context_version: str = ""
    db_schema_version: str = ""
    generated_sql: str | None = None
    tables_referenced: list[str] = field(default_factory=list)
    row_count: int | None = None
    answer_value: float | None = None     # the answer, when it is a single number
    latency_ms: int | None = None
    usage: dict[str, int] = field(default_factory=dict)    # tokens: input, output, cache read/write
    refusal: str | None = None
    error: str | None = None
    user_feedback: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.ts:
            self.ts = datetime.now(timezone.utc).isoformat(timespec="seconds")

    def write(self, path: Path = TRACE_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as fh:
            fh.write(json.dumps(asdict(self), separators=(",", ":")) + "\n")


def read_traces(path: Path = TRACE_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


class timer:
    """with timer() as t: ...  -> t.ms"""

    def __enter__(self):
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.ms = int((time.perf_counter() - self._t0) * 1000)
        return False
