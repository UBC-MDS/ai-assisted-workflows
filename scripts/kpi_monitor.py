"""KPI drift monitor. Run after every deploy.

For each scheduled report, compares the newest release's answer with that report's history.
Every report covers a closed period — a finished cohort, a past quarter — so its answer has
no business changing. Any move larger than the tolerance is flagged, in either direction.

If ops/kpi_baseline.json exists, it is the approved baseline: a human signed off on those
values, and they replace the history median.

Prints a markdown report. Exits 1 if anything drifted.

    python scripts/kpi_monitor.py
    python scripts/kpi_monitor.py --markdown-out kpi.md
"""

import argparse
import json
import statistics
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from askdb import __version__  # noqa: E402
from askdb.trace import read_traces  # noqa: E402

TOLERANCE = 0.005   # 0.5% relative


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", default=__version__)
    ap.add_argument("--markdown-out")
    args = ap.parse_args()

    reports = yaml.safe_load((ROOT / "ops" / "scheduled_reports.yaml").read_text())["reports"]
    approved_file = ROOT / "ops" / "kpi_baseline.json"
    approved = json.loads(approved_file.read_text())["reports"] if approved_file.exists() else {}
    traces = [t for t in read_traces() if t.get("source") == "scheduled_report"]

    rows, drifted = [], []
    for rep in reports:
        mine = [t for t in traces if t.get("report_id") == rep["id"]]
        history = [t["answer_value"] for t in mine
                   if t.get("release") != args.release and t.get("answer_value") is not None]
        latest = [t for t in mine if t.get("release") == args.release]
        if rep["id"] in approved:
            history = [approved[rep["id"]]]
        if not history or not latest:
            rows.append((rep["label"], "—", "—", "no data"))
            continue
        base = statistics.median(history)
        now = latest[-1].get("answer_value")
        if now is None:
            status = "⚠️ no answer" + (f" ({latest[-1]['error']})" if latest[-1].get("error") else "")
            drifted.append(rep["label"])
            rows.append((rep["label"], f"{base:,.2f}", "—", status))
            continue
        change = (now - base) / abs(base) if base else float("inf")
        flag = abs(change) > TOLERANCE
        if flag:
            drifted.append(rep["label"])
        shown = f"{now - base:+.1f} pts" if rep["label"].endswith("(%)") else f"{change:+.1%}"
        rows.append((rep["label"], f"{base:,.2f}", f"{now:,.2f}", f"{'⚠️ ' if flag else ''}{shown}"))

    lines = [f"## KPI drift check — release {args.release}", "",
             "Every report below covers a closed period. Its answer should not change between releases.", "",
             f"| Report | {'Approved baseline' if approved else 'History (median)'} | This release | Change |",
             "|---|---|---|---|"]
    lines += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in rows]
    lines += ["", f"**{len(drifted)} of {len(reports)} reports drifted.**" if drifted
              else "No drift."]
    out = "\n".join(lines)
    print(out)
    if args.markdown_out:
        Path(args.markdown_out).write_text(out + "\n")
    return 1 if drifted else 0


if __name__ == "__main__":
    raise SystemExit(main())
