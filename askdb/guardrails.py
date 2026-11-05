"""Guardrails applied around every askdb request.

Three hooks, called by pipeline.ask() in this order:

    check_question(question)          before the model is called    -> refusal text or None
    check_sql(sql)                    before the SQL is executed    -> raises on violation
    filter_result(columns, rows)      before rows are returned      -> (columns, rows)
"""

import re

MAX_QUESTION_CHARS = 500
MAX_ROWS = 1000

_WRITE_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH|DETACH|PRAGMA|VACUUM)\b", re.I
)


def check_question(question: str) -> str | None:
    if len(question) > MAX_QUESTION_CHARS:
        return f"Questions are limited to {MAX_QUESTION_CHARS} characters."
    return None


def check_sql(sql: str) -> None:
    head = sql.lstrip().upper()
    if not (head.startswith("SELECT") or head.startswith("WITH")):
        raise ValueError(f"refusing to run non-SELECT statement: {sql[:60]}")
    if _WRITE_KEYWORDS.search(sql):
        raise ValueError(f"refusing to run statement with a write keyword: {sql[:60]}")


def filter_result(columns: list[str], rows: list[tuple]) -> tuple[list[str], list[tuple]]:
    return columns, rows[:MAX_ROWS]
