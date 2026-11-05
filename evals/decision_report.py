"""Where do runs disagree — with each other, and with the business requirements?

    python evals/decision_report.py --tag before
    python evals/decision_report.py --tag after --questions questions.yaml

For each question: how many distinct answers came back, and, decision by decision, which
values the runs chose. ⚠️ marks decisions the runs disagree on; ❌ marks values that contradict
the question's expected decisions (from --questions, entries of {question, expected}).
"""

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ["time_basis", "reference_date", "period_start", "period_end", "money_measure", "refunds", "currency", "invoice_status",
          "account_types", "acquired_store", "erased_customers", "output_format"]


def norm_date(v):
    """Accept 2025-08-01, 2025-08 or 'August 1, 2025'; return YYYY-MM-DD (or the input)."""
    if not isinstance(v, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return v
    for fmt in ("%Y-%m", "%B %d, %Y", "%b %d, %Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(v, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return v


def norm(rows):
    return json.dumps([[round(c, 2) if isinstance(c, float) else c for c in r] for r in rows], default=str)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="latest")
    ap.add_argument("--questions", help="YAML list of {question, expected: {field: value}}")
    args = ap.parse_args()

    expectations = {}
    if args.questions:
        data = yaml.safe_load(Path(args.questions).read_text())
        for q in (data["questions"] if isinstance(data, dict) else data):
            if isinstance(q, dict):
                expectations[q["question"]] = q.get("expected") or {}
    files = sorted((ROOT / "runs" / args.tag).glob("*.jsonl"))
    consistent = total = runs_ok = runs_total = 0
    for f in files:
        runs = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
        answers = Counter(norm(r["rows"]) if not r["error"] else "ERROR" for r in runs)
        total += 1
        consistent += len(answers) == 1
        expected = expectations.get(runs[0]["question"], {})
        print(f"\n## {runs[0]['question']}")
        print(f"{len(runs)} runs, {len(answers)} distinct answer(s): "
              + "; ".join(f"{a[:60]} ×{n}" for a, n in answers.most_common()))
        failed = [r for r in runs if r["error"] or r.get("refusal")]
        if failed:
            print(f"{len(failed)} run(s) failed or were refused: " + "; ".join((r['error'] or r['refusal'])[:80] for r in failed))
        decided = [r for r in runs if r.get("decisions")]
        if not decided:
            print("(no decisions extracted yet — run evals/extract_decisions.py)")
            continue
        print("\n| decision | values across runs | |\n|---|---|---|")
        for field in FIELDS:
            vals = Counter(str(norm_date(r["decisions"].get(field)) if field.startswith("period")
                               else r["decisions"].get(field)) for r in decided)
            flags = ""
            if len(vals) > 1:
                flags += "⚠️ runs disagree "
            want = expected.get(field)
            allowed = {str(w) for w in (want if isinstance(want, list) else [want])} | {"not_applicable"}
            if want is not None and any(v not in allowed for v in vals):
                flags += f"❌ expected {' or '.join(map(str, want)) if isinstance(want, list) else want}"
            print(f"| {field} | {', '.join(f'{v} ×{n}' for v, n in vals.most_common())} | {flags} |")
        if expected:
            for r in runs:
                d = r.get("decisions") or {}
                d = {k: norm_date(v) if k.startswith("period") else v for k, v in d.items()}
                ok = all(d.get(k) in [*(v if isinstance(v, list) else [v]), "not_applicable", None]
                         for k, v in expected.items())
                runs_ok += ok
                runs_total += 1

    print(f"\n**{consistent} of {total} questions gave the same answer on every run.**")
    if expectations and runs_total:
        print(f"**{runs_ok} of {runs_total} runs ({runs_ok / runs_total:.0%}) match every expected decision.**")


if __name__ == "__main__":
    main()
