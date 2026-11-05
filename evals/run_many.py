"""Ask askdb the same question several times and keep every answer.

    python evals/run_many.py --question "What was revenue last quarter?" --runs 5
    python evals/run_many.py --file questions.yaml --runs 5 --tag before

The file is a YAML list of questions — plain strings, or {question, expected} entries.

Writes runs/<tag>/<question-slug>.jsonl, one line per run: the SQL, the answer, any error.
"""

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from askdb.pipeline import MODEL, PROVIDER, ask, load_schema_context  # noqa: E402


def slug(question: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", question.lower()).strip("-")[:60]


def one_run(question: str, n: int) -> dict:
    try:
        r = ask(question, write_trace=False)
        return {"run": n, "sql": r["sql"], "columns": r["columns"], "rows": r["rows"][:50],
                "refusal": r["refusal"], "error": None}
    except Exception as exc:
        return {"run": n, "sql": None, "columns": [], "rows": [], "refusal": None,
                "error": f"{type(exc).__name__}: {exc}"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--question")
    ap.add_argument("--file", help="YAML list of questions, or {questions: [...]}")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--tag", default="latest", help="label for this batch, e.g. before / after")
    ap.add_argument("--workers", type=int, default=1 if PROVIDER == "ollama" else 8)
    args = ap.parse_args()

    if args.file:
        data = yaml.safe_load(Path(args.file).read_text())
        questions = data["questions"] if isinstance(data, dict) else data
        questions = [q["question"] if isinstance(q, dict) else q for q in questions]
    elif args.question:
        questions = [args.question]
    else:
        ap.error("give --question or --file")

    out_dir = ROOT / "runs" / args.tag
    out_dir.mkdir(parents=True, exist_ok=True)
    _, docs_version = load_schema_context()
    for q in questions:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            runs = list(pool.map(lambda n: one_run(q, n), range(1, args.runs + 1)))
        path = out_dir / f"{slug(q)}.jsonl"
        with path.open("w") as fh:
            for r in runs:
                fh.write(json.dumps({"question": q, "model": MODEL, "docs_version": docs_version, **r},
                                    default=str, ensure_ascii=False) + "\n")
        answers = {json.dumps(r["rows"], default=str) for r in runs if not r["error"]}
        print(f"{len(answers)} distinct answer(s) in {len(runs)} runs  —  {q}")
    print(f"\nsaved to {out_dir.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
