# ai-assisted-workflows

Hands-on workshop materials on modern AI-assisted software development workflows, covering problem framing, agentic coding, testing, evaluation, and production best practices.

The workshop is built around **askdb**, a small production-style service described below. Workshop exercises are in `workshop/`.

---

## askdb

Natural-language analytics for the data team. Ask a question in English, get an answer from
the company warehouse.

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
python -m askdb "what was revenue last month?"
```

```
SELECT ROUND(SUM((i.Subtotal - COALESCE(rf.Refunded, 0)) * x.RateToUSD), 2) ...

  revenue
  8063.5

trace 3f9a1c0e7b2d
```

### How it works

```
question → guardrails → schema docs + LLM writes SQL → guardrails → execute → trace
```

The model never sees the data. It sees `askdb/schema_context/` — the table docs, the metric
definitions, and who counts as a customer — writes one SQL query, and askdb runs it read-only
against `data/askdb.sqlite`. Every request is logged to `logs/traces.jsonl`.

### Shipping a change

| Stage | What runs | Where |
|---|---|---|
| PR opened | Benchmark gate — 40 question/gold-SQL pairs, graded by comparing results | `eval-gate.yml` |
| PR opened | Privacy review — deterministic checks + LLM checklist review | `pr-review.yml` |
| Merged to `main` | Deploy — replay production traffic, KPI drift monitor, incident if anything moved | `deploy.yml` |
| Issue labelled `question` | KB bot answers from `docs/` | `kb-responder.yml` |

### Repo

| Path | |
|---|---|
| `askdb/` | the service |
| `data/askdb.sqlite` | the warehouse: 6 stores, ~6,000 customers, ~78k invoices, 2022–2025 |
| `docs/` | FAQ, runbook, PRDs |
| `evals/` | benchmark and harness |
| `ops/` | scheduled reports and the traffic sample replayed on deploy |
| `scripts/` | deploy tooling, review bot, data builders |
| `logs/traces.jsonl` | six weeks of production traces |
| `workshop/participant/` | guide for workshop participants |

The music catalogue is the public [Chinook](https://github.com/lerocha/chinook-database) sample
database. Customers, invoices and everything else are synthetic.
