"""askdb — ask a question in English, get an answer from the company warehouse.

question → guardrails → schema docs + LLM writes SQL → guardrails → execute → trace

Small on purpose: someone watching a screen share should be able to read this end to end.
"""

import hashlib
import json
import os
import re
import sqlite3
import urllib.request
from pathlib import Path

import anthropic

from . import __version__, guardrails
from .trace import Trace, timer

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "askdb.sqlite"
SCHEMA_CONTEXT = Path(os.environ.get("ASKDB_SCHEMA_DIR", Path(__file__).resolve().parent / "schema_context"))

# ASKDB_PROVIDER=ollama runs a local model through Ollama instead of the Claude API.
PROVIDER = os.environ.get("ASKDB_PROVIDER", "anthropic")
MODEL = os.environ.get("ASKDB_MODEL", "claude-sonnet-5-5" if PROVIDER == "anthropic" else "qwen2.5-coder:14b")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")

SYSTEM = """\
You write SQLite queries for askdb, the analytics assistant at a music retailer.

The documentation below is the only description of the warehouse you have. Follow its
definitions and filters exactly — they are how the business reports its numbers — and do not
invent tables or columns it does not mention.

Return one SELECT statement (CTEs allowed). No writes, no explanation.

{schema}
"""

SQL_FORMAT = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {"sql": {"type": "string", "description": "One SQLite SELECT statement."}},
        "required": ["sql"],
        "additionalProperties": False,
    },
}


def load_schema_context() -> tuple[str, str]:
    """Concatenate the schema docs. Returns (text, version); the version is a content hash,
    so every trace records exactly which docs produced its SQL."""
    docs = sorted(SCHEMA_CONTEXT.glob("*.md"))
    text = "\n\n---\n\n".join(d.read_text() for d in docs)
    return text, "sc-" + hashlib.sha256(text.encode()).hexdigest()[:8]


def db_schema_version() -> str:
    """Fingerprint of the warehouse's actual schema, independent of the docs."""
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        ddl = "\n".join(r[0] for r in con.execute(
            "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY name"))
    finally:
        con.close()
    return "db-" + hashlib.sha256(ddl.encode()).hexdigest()[:8]


def complete_json(system: str, user: str, schema: dict) -> tuple[dict, dict]:
    """One model call whose reply must match a JSON schema. Returns (reply, token usage).

    The system prompt is cached on the Claude API; with ASKDB_PROVIDER=ollama it runs locally.
    """
    if PROVIDER == "ollama":
        body = {"model": MODEL, "stream": False, "format": schema,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "options": {"num_ctx": 16384}}   # Ollama's default window would silently cut the docs off
        req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            data = json.load(r)
        usage = {"input_tokens": data.get("prompt_eval_count", 0), "output_tokens": data.get("eval_count", 0),
                 "cache_read_tokens": 0, "cache_write_tokens": 0}
        return json.loads(data["message"]["content"]), usage

    response = anthropic.Anthropic().messages.create(
        model=MODEL,
        max_tokens=4000,
        # Cache the system prompt: identical on every call, so only the first call in five minutes pays for it.
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        output_config={"format": {"type": "json_schema", "schema": schema}, "effort": "medium"},
        messages=[{"role": "user", "content": user}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"model declined: {response.stop_details}")
    text = next(b.text for b in response.content if b.type == "text")
    u = response.usage
    usage = {"input_tokens": u.input_tokens, "output_tokens": u.output_tokens,
             "cache_read_tokens": u.cache_read_input_tokens or 0,
             "cache_write_tokens": u.cache_creation_input_tokens or 0}
    return json.loads(text), usage


def generate_sql(question: str, schema: str) -> tuple[str, dict]:
    reply, usage = complete_json(SYSTEM.format(schema=schema), question, SQL_FORMAT["schema"])
    return reply["sql"].strip(), usage


def execute(sql: str) -> tuple[list[str], list[tuple]]:
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        cur = con.execute(sql)
        return [d[0] for d in cur.description], cur.fetchall()
    finally:
        con.close()


def tables_referenced(sql: str) -> list[str]:
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    finally:
        con.close()
    return sorted(t for t in tables if re.search(rf"\b{t}\b", sql, re.I))


def scalar(rows: list[tuple]) -> float | None:
    """The answer as one number, when the answer is one number."""
    if len(rows) == 1 and len(rows[0]) == 1 and isinstance(rows[0][0], (int, float)):
        return float(rows[0][0])
    return None


def ask(question: str, *, source: str = "adhoc", report_id: str | None = None,
        write_trace: bool = True) -> dict:
    schema, version = load_schema_context()
    trace = Trace(question=question, model=MODEL, release=__version__, source=source,
                  report_id=report_id, schema_context_version=version,
                  db_schema_version=db_schema_version())
    result = {"sql": None, "columns": [], "rows": [], "refusal": None, "trace_id": trace.trace_id}
    try:
        with timer() as t:
            refusal = guardrails.check_question(question)
            if refusal:
                result["refusal"] = trace.refusal = refusal
                return result
            sql, trace.usage = generate_sql(question, schema)
            guardrails.check_sql(sql)
            columns, rows = guardrails.filter_result(*execute(sql))
        result.update(sql=sql, columns=columns, rows=rows)
        trace.generated_sql, trace.row_count, trace.latency_ms = sql, len(rows), t.ms
        trace.tables_referenced = tables_referenced(sql)
        trace.answer_value = scalar(rows)
        return result
    except Exception as exc:
        trace.error = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        if write_trace:
            trace.write()
