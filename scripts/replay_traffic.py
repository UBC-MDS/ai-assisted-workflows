"""Replay production traffic through the current askdb — what a deploy does.

Runs every scheduled report (ops/scheduled_reports.yaml) and every sampled user question
(ops/traffic_sample.yaml) through askdb.ask(). Each request appends a trace to
logs/traces.jsonl, tagged with the current release.

    python scripts/replay_traffic.py              # ~50 live model calls
    python scripts/replay_traffic.py --workers 4
"""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from askdb import __version__  # noqa: E402
from askdb.pipeline import ask  # noqa: E402

OPS = ROOT / "ops"


def load_requests():
    reports = yaml.safe_load((OPS / "scheduled_reports.yaml").read_text())["reports"]
    adhoc = yaml.safe_load((OPS / "traffic_sample.yaml").read_text())["questions"]
    return ([(r["question"], "scheduled_report", r["id"]) for r in reports]
            + [(q, "adhoc", None) for q in adhoc])


def run(req):
    question, source, report_id = req
    try:
        r = ask(question, source=source, report_id=report_id)
        return "refused" if r["refusal"] else "ok"
    except Exception:
        return "error"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    reqs = load_requests()
    print(f"replaying {len(reqs)} requests against askdb {__version__} ...")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        outcomes = list(pool.map(run, reqs))
    print({k: outcomes.count(k) for k in ("ok", "refused", "error")})


if __name__ == "__main__":
    main()
