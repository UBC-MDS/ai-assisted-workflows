"""Check that a change implements the 2.4 PRD (docs/prd/2.4-gdpr-erasure.md).

Run it before opening the PR. Security-approved code (SEC-2291) is checked word for word;
the rest are checked by behaviour, so any correct implementation passes.

    python scripts/check_release.py
"""

import importlib
import re
import sqlite3
import sys
import unittest
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

POPULATION = ROOT / "askdb/schema_context/customer_population.md"
PATTERN = 'EMAIL_PATTERN = re.compile(r"[a-z0-9._%-]+@[a-z0-9.-]+\\.[a-z]{2,}")'
REFUSAL = "This customer's data has been erased under GDPR and cannot be shown."

results = []


def check(item, ok, fix=""):
    results.append(ok)
    print(f"  {'✅' if ok else '❌'} {item}" + ("" if ok else f"\n       → {fix}"))


def flat(s):
    return " ".join(s.split())


def main():
    print("Checking release 2.4 against docs/prd/2.4-gdpr-erasure.md\n")
    con = sqlite3.connect(f"file:{ROOT / 'data/askdb.sqlite'}?mode=ro", uri=True)
    # A retail customer whose latest erasure request is completed: erased under any reading.
    erased_id, erased_email, erased_phone = con.execute("""
        SELECT c.CustomerId, c.Email, c.Phone FROM Customer c JOIN ErasureRequest r ON r.CustomerId = c.CustomerId
        WHERE c.AccountType = 'retail' AND r.Status = 'completed'
          AND r.RequestId = (SELECT MAX(RequestId) FROM ErasureRequest x WHERE x.CustomerId = c.CustomerId)
        ORDER BY c.CustomerId LIMIT 1""").fetchone()

    # 1 — erased customers out of the shared customer definition
    filt = POPULATION.read_text().split("Canonical filter", 1)[-1]
    check("1. customer definition excludes erased customers", "ErasureRequest" in filt,
          "erased customers must not be counted or listed: build it into the customer definition")

    # 2, 3 — behaviour
    guardrails = importlib.import_module("askdb.guardrails")
    _, rows = guardrails.filter_result(["Email", "Phone", "Note"], [(erased_email.upper(), erased_phone, "ok")])
    leaked = [v for v in rows[0] if str(v).lower() in {erased_email.lower(), erased_phone.lower()}]
    check("2. erased customer's personal data masked", not leaked,
          "filter_result() must hide an erased customer's email, phone and address")
    check("3. lookup by customer ID refused",
          guardrails.check_question(f"What is the email for customer {erased_id}?") == REFUSAL,
          "check_question() must refuse questions naming an erased customer by number, with the PRD's message")
    check("3. lookup by email refused (any case)",
          guardrails.check_question(f"Orders for {erased_email.swapcase()}") == REFUSAL,
          "check_question() must refuse questions naming an erased customer by email, any letter case")
    check("3. ordinary questions still answered",
          guardrails.check_question("What was revenue last month?") is None,
          "check_question() is refusing questions it shouldn't")

    # 4 — verbatim pattern + tests
    trace_src = (ROOT / "askdb/trace.py").read_text()
    check("4. SEC-2291 pattern present (verbatim)", PATTERN in trace_src,
          "use EMAIL_PATTERN exactly as written in docs/security/SEC-2291-email-redaction.md")
    check("4. redact() applied before traces are written",
          "redact(" in trace_src.split("def write", 1)[-1] if "def write" in trace_src else False,
          "call redact() on the question text inside Trace.write()")
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    ran = unittest.TextTestRunner(stream=open("/dev/null", "w")).run(suite)
    check("4. tests/test_redact.py present and passing",
          (ROOT / "tests/test_redact.py").exists() and ran.wasSuccessful(),
          "add SEC-2291's required tests as tests/test_redact.py; run python -m unittest discover tests")

    # 5
    faq = (ROOT / "docs/faq.md").read_text().lower()
    check("5. FAQ explains erasure", "eras" in faq, "add an FAQ entry about erased customers")

    # 6
    pairs = yaml.safe_load((ROOT / "evals/benchmark.yaml").read_text())["pairs"]
    expects = {p.get("expect") for p in pairs}
    check("6. refusal and personal-data pairs added", {"refusal", "no_erased_pii"} <= expects,
          "add at least one expect: refusal and one expect: no_erased_pii pair")
    cust = [p for p in pairs if p["category"] == "customer"]
    check("6. customer pairs updated for erasure",
          bool(cust) and all("ErasureRequest" in p["gold_sql"] for p in cust),
          "every customer-count pair's correct answer changes; update its gold_sql")

    # 7
    init = (ROOT / "askdb/__init__.py").read_text()
    check("release: version is 2.4.0", '__version__ = "2.4.0"' in init, 'set __version__ = "2.4.0"')

    print(f"\n{sum(results)}/{len(results)} checks passed.")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
