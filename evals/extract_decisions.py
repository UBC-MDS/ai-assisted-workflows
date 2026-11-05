"""Read the SQL from each run and record the business decisions it made.

    python evals/extract_decisions.py --tag before

Adds a "decisions" object to every run in runs/<tag>/*.jsonl, filled in against a fixed
checklist, so runs can be compared decision by decision. The extractor is a model too:
spot-check its work.

The extractor can use a different model from askdb, e.g. askdb on a local model and extraction
on Claude:  EXTRACT_PROVIDER=anthropic EXTRACT_MODEL=claude-haiku-5-5 python evals/extract_decisions.py
"""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from askdb import pipeline  # noqa: E402

# Point the shared model call at the extractor's own provider/model, if set.
pipeline.PROVIDER = os.environ.get("EXTRACT_PROVIDER", pipeline.PROVIDER)
pipeline.MODEL = os.environ.get("EXTRACT_MODEL", pipeline.MODEL if "EXTRACT_PROVIDER" not in os.environ
                                else ("claude-haiku-5-5" if pipeline.PROVIDER == "anthropic" else "qwen2.5-coder:14b"))
complete_json = pipeline.complete_json

CHECKLIST = {
    "time_basis": ["fiscal", "calendar", "no_time_filter", "unclear"],
    "reference_date": ["data_as_of_2025_12_31", "system_today", "explicit_dates_only", "not_applicable"],
    "money_measure": ["net_subtotal", "total_including_tax", "line_revenue", "rollup_net_revenue", "not_money"],
    "refunds": ["subtracted", "ignored", "not_applicable"],
    "currency": ["converted_to_usd", "local_currency", "not_applicable"],
    "invoice_status": ["settled_only", "includes_pending", "all_statuses", "not_applicable"],
    "account_types": ["retail_and_reseller", "retail_only", "reseller_only", "all_including_internal_and_test",
                      "not_applicable"],
    "acquired_store": ["pre_acquisition_sales_excluded", "pre_acquisition_customers_excluded", "not_handled",
                       "not_applicable"],
    "erased_customers": ["excluded", "included", "not_applicable"],
    "output_format": ["percentage", "fraction", "currency_amount", "count", "list", "other"],
}

SCHEMA = {
    "type": "object",
    "properties": {
        **{k: {"type": "string", "enum": v} for k, v in CHECKLIST.items()},
        "period_start": {"type": "string", "pattern": "^(\\d{4}-\\d{2}-\\d{2}|none)$",
                         "description": "First date included, YYYY-MM-DD, or 'none'."},
        "period_end": {"type": "string", "pattern": "^(\\d{4}-\\d{2}-\\d{2}|none)$",
                       "description": "Last date included, YYYY-MM-DD, or 'none'."},
        "other_assumptions": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
    },
    "required": [*CHECKLIST, "period_start", "period_end", "other_assumptions"],
    "additionalProperties": False,
}

SYSTEM = """\
You audit SQL written against a music retailer's warehouse. Given a question and the SQL that
answered it, record the business decisions the SQL ACTUALLY makes — not what it should make.

Warehouse facts you need:
- Invoice.Subtotal is pre-tax; Invoice.Total includes tax. InvoiceLine holds line prices.
- Invoice.InvoiceStatus: settled, pending, void, comped. Refund holds refunds per invoice.
- Amounts are in local currency; ExchangeRate converts to USD by month.
- FiscalMonth maps months to fiscal years/quarters; the fiscal year starts 1 February.
- MonthlyRevenueRollup.NetRevenueUSD is pre-aggregated net revenue (settled, USD, refunds and
  internal/test accounts already handled).
- Customer.AccountType: retail, reseller, internal, test. ErasureRequest logs GDPR erasure requests by status.
- Store.AcquiredDate is set for the acquired São Paulo store.
- The data runs to 2025-12-31. reference_date records what the SQL treats as "today": that date,
  the system clock (date('now') etc.), or only fixed dates written into the query.

period_start and period_end are the first and LAST dates INCLUDED: for
"InvoiceDate >= '2023-01-01' AND InvoiceDate < '2024-01-01'" write 2023-01-01 and 2023-12-31.

Use not_applicable when a decision does not arise for this question. Use "unclear" only when
the SQL genuinely does not determine it. List up to three other notable assumptions.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="latest")
    ap.add_argument("--force", action="store_true", help="re-extract runs that already have decisions")
    args = ap.parse_args()

    files = sorted((ROOT / "runs" / args.tag).glob("*.jsonl"))
    if not files:
        raise SystemExit(f"no runs in runs/{args.tag}/ — run evals/run_many.py first")
    for f in files:
        runs = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
        for r in runs:
            if r.get("decisions") and not args.force:
                continue
            if not r.get("sql"):
                r["decisions"] = None
                continue
            r["decisions"], _ = complete_json(SYSTEM, f"Question: {r['question']}\n\nSQL:\n{r['sql']}", SCHEMA)
        f.write_text("".join(json.dumps(r, ensure_ascii=False, default=str) + "\n" for r in runs))
        print(f"extracted {len(runs)} runs  —  {runs[0]['question']}")


if __name__ == "__main__":
    main()
