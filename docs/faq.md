# askdb FAQ

Answers to the questions the data team gets every week. The KB bot
(`.github/workflows/kb-responder.yml`) answers new `question`-labelled issues from this file
and the rest of `docs/`.

## How do I ask askdb a question?

```bash
python -m askdb "what was revenue last month?"
```

It prints the SQL it wrote, the rows, and a trace id. Every request appends one line to
`logs/traces.jsonl`.

## Where does the data come from?

`data/askdb.sqlite`, a read-only copy of the warehouse, refreshed nightly. Data is as of
2025-12-31.

## How does askdb know what the tables mean?

Every file in `askdb/schema_context/` is included in the model's instructions. Those docs are
its entire picture of the warehouse: table meanings, metric definitions, and who counts as a
customer. If something isn't described there, askdb doesn't know it.

## What does "revenue" mean?

Net product revenue in USD: settled invoices, tax-exclusive, net of refunds, converted at the
invoice month's exchange rate, excluding internal and test accounts. Owned by finance. See
`askdb/schema_context/metrics.md`.

## Who counts as a customer?

Defined once in `askdb/schema_context/customer_population.md` and used by every customer
metric: retail and reseller accounts only, excluding São Paulo customers acquired with the
store.

## Why is "Q1" not January to March?

Our fiscal year starts on 1 February. "Q1" means fiscal Q1 (Feb–Apr) unless you say
"calendar".

## How do I find the query behind an answer?

Take the trace id printed with the answer and search `logs/traces.jsonl` for it. Each trace
records the SQL, the tables it touched, the release, and the version of the schema docs used.

## How do I check askdb's answers are right?

```bash
python evals/run_eval.py
```

Runs the benchmark: questions with known-correct SQL, graded by comparing results.

## Who do I ask about something not covered here?

Open an issue without the `question` label; the data team triages them daily.
