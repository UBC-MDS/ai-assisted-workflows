# CLAUDE.md

## What this repo is

**askdb** — the analytics assistant used by the data team at a music retailer. Ask a question in
English, get an answer from the company warehouse:

```
question → guardrails → schema docs + LLM writes SQL → guardrails → execute on SQLite → trace
```

It is in production. Changes ship through PRs, a benchmark gate, a privacy review, and a deploy
that replays production traffic and monitors the exec KPI reports.

## Layout

```
askdb/
  pipeline.py           ask(): the whole request path
  guardrails.py         checks before the model, before execution, and on results
  trace.py              one JSON line per request → logs/traces.jsonl
  schema_context/       the docs the model reads: tables, metric definitions, who counts as a customer
data/askdb.sqlite       the warehouse (read-only; built by scripts/build_db.py)
docs/                   FAQ + runbook (the KB bot answers from these)
docs/prd/               product requirement documents
docs/security/          Security standards (approved code to use verbatim)
evals/                  benchmark.yaml, run_eval.py, baseline.json
ops/                    scheduled_reports.yaml (exec KPI report), traffic_sample.yaml
scripts/                replay_traffic.py, kpi_monitor.py, check_release.py, bot.py, builders
tests/                  unit tests (python -m unittest discover tests)
.github/workflows/      eval gate, privacy review, deploy, KB responder
```

## API key

askdb reads `ANTHROPIC_API_KEY` from `.env` in the repo root (gitignored) if it isn't already in
the environment.

## Working on a PRD

- **Implement PRDs exactly as specified.** Text that Legal or Security have approved — such as a
  Security standard in `docs/security/` — is used word for word: do not rephrase, reformat or
  improve it.
- **Don't decide what a PRD means yourself.** If a PRD requirement can be read more than one
  way, conflicts with the data, or conflicts with another document, stop before implementing
  that part. List the readings and ask the person you're working with to choose. Record their
  decision in the PR description.
- Don't expand scope beyond what the PRD asks.
- A release sets `__version__` in `askdb/__init__.py` to the release number (askdb 2.4 →
  `"2.4.0"`). Deploys only run when it changes. User-facing behaviour changes go in `docs/faq.md`.
- Before opening a PR, run:

```bash
python scripts/check_release.py          # does the change match the PRD?
python -m unittest discover tests
python evals/run_eval.py --gate          # live model; ~40 calls
```

## Conventions

- Python 3.11+, stdlib + `anthropic` + `pyyaml` only. No frameworks.
- Everything is a file: SQLite for data, JSONL for traces, YAML for the benchmark.
- Evals compare result sets, never SQL text. No LLM judge in the grading path.
- The warehouse is read-only to askdb. `scripts/build_db.py` and `scripts/generate_history.py`
  are build tools, not part of normal changes.

## Commands

```bash
python -m askdb "what was revenue last month?"
python evals/run_eval.py --category customer
python scripts/replay_traffic.py && python scripts/kpi_monitor.py    # what a deploy runs
```
