"""Build logs/traces.jsonl — six weeks of production history for release 2.3.0.

LAYER 0 ONLY. Run once against the live model before the workshop; the output is committed.

History is made of REAL askdb runs, not invented numbers: every scheduled report and every
sampled question is run through askdb several times, then the runs are laid out over six
weeks — reports every morning, user questions through the working day. So the only
difference between history and a later deploy is whatever the deploy changed.

    python scripts/generate_history.py                       # live: ~70 model calls
    python scripts/generate_history.py --raw runs.jsonl      # lay out existing raw runs
"""

import argparse
import json
import os
import random
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "logs" / "traces.jsonl"
SEED = 20261017
USERS = ["finance.priya", "finance.tom", "ops.dana", "mktg.chen", "exec.ryan", "support.kim",
         "crm.lena", "analytics.omar"]


def live_runs(report_runs, adhoc_runs):
    raw = Path(tempfile.mkstemp(suffix=".jsonl")[1])
    os.environ["ASKDB_TRACE_PATH"] = str(raw)
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "scripts"))
    from concurrent.futures import ThreadPoolExecutor
    from replay_traffic import load_requests, run
    from askdb.pipeline import ask
    ask("How many stores do we have?", write_trace=False)      # warm the prompt cache once
    reqs = [r for r in load_requests() if r[1] == "scheduled_report"] * report_runs \
         + [r for r in load_requests() if r[1] == "adhoc"] * adhoc_runs
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(run, reqs))
    return raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-runs", type=int, default=3, help="runs per scheduled report (checks stability)")
    ap.add_argument("--adhoc-runs", type=int, default=1)
    ap.add_argument("--raw", help="existing raw run traces to lay out instead of calling the model")
    ap.add_argument("--end", default=(date.today() - timedelta(days=1)).isoformat())
    ap.add_argument("--days", type=int, default=42)
    args = ap.parse_args()

    raw = Path(args.raw) if args.raw else live_runs(args.report_runs, args.adhoc_runs)
    print(f"raw runs: {raw}")
    runs = [json.loads(l) for l in raw.read_text().splitlines() if l.strip()]
    by_key = {}
    for r in runs:
        by_key.setdefault((r["source"], r.get("report_id"), r["question"]), []).append(r)
    reports = sorted(k for k in by_key if k[0] == "scheduled_report")
    adhoc = sorted(k for k in by_key if k[0] == "adhoc")

    rng = random.Random(SEED)
    end = date.fromisoformat(args.end)
    out = []
    for d in range(args.days):
        day = end - timedelta(days=args.days - 1 - d)
        stamp = lambda h, m: datetime(day.year, day.month, day.day, h, m, rng.randint(0, 59), tzinfo=timezone.utc)
        for k in reports:                                     # every morning at 07:00
            out.append((stamp(7, rng.randint(0, 4)), rng.choice(by_key[k]), None))
        if day.weekday() < 5:                                 # users ask during the working day
            for k in rng.sample(adhoc, rng.randint(8, 14)):
                out.append((stamp(rng.randint(9, 17), rng.randint(0, 59)), rng.choice(by_key[k]), rng.choice(USERS)))

    out.sort(key=lambda x: x[0])
    with OUT.open("w") as fh:
        for ts, run, user in out:
            t = dict(run)
            t["ts"] = ts.isoformat(timespec="seconds")
            t["trace_id"] = f"{rng.getrandbits(48):012x}"
            t["latency_ms"] = max(400, int((run.get("latency_ms") or 2500) * rng.uniform(0.8, 1.25)))
            t["extra"] = {"user": user or "kpi-report-bot"}
            fh.write(json.dumps(t, separators=(",", ":"), ensure_ascii=False) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(out)} traces, {args.days} days ending {end}, "
          f"from {len(runs)} raw runs")


if __name__ == "__main__":
    main()
