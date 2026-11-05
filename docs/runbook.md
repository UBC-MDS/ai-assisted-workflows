# askdb operational runbook

## Service summary

| | |
|---|---|
| **What** | Natural-language analytics over the company warehouse |
| **Customer** | The data team, fielding ad-hoc questions from finance, ops, marketing and execs |
| **Pain it removes** | Hundreds of repeat "what was X last quarter" requests a month |
| **Success metric** | Deflection rate, plus answer correctness on `evals/benchmark.yaml` |
| **Explicitly not the metric** | "The model looks good" |

## Release process

1. Change on a branch; open a PR.
2. **Eval gate** (`eval-gate.yml`) runs the benchmark. Merge is blocked if a category loses
   two or more pairs against `evals/baseline.json`.
3. **Privacy review** (`pr-review.yml`) must approve.
4. Merge to `main` **is** a deploy (`deploy.yml`): production traffic is replayed through the
   new release and the KPI drift monitor checks the scheduled reports.

## What pages you

| Signal | From | Meaning |
|---|---|---|
| KPI drift | `deploy.yml` → `scripts/kpi_monitor.py` | A scheduled report about a **closed period** changed its answer after a release. Closed periods should never change — something about how we measure moved. |
| Eval gate failure | `eval-gate.yml` | A change under review regressed a benchmark category. |
| Error rate | traces | A real outage. Rare. |

## Investigating a KPI drift

1. Which reports moved, and which didn't? The pattern of what *didn't* move is evidence too.
2. Compare traces for the same question before and after the release
   (`release`, `generated_sql`, `tables_referenced`, `answer_value`).
3. Check `schema_context_version` — did the docs the model reads change in this release?
4. Read the release's diff.
