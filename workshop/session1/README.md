# Session 1 — Business definitions for askdb

## The situation

askdb is now the company's reporting tool. Every number in every metrics report comes from
asking askdb a question. There is no other source to check it against.

Each of the ten questions in `questions.yaml` was asked **five times**, word for word the same.
askdb wrote different SQL each time, and mostly got a different answer.

The model is not the main problem. The questions are ambiguous, and nothing in askdb's
documentation (`askdb/schema_context/*.md`) tells it how the business resolves the ambiguity: what "last
quarter" means, what counts as an order, whether a rate is by amount or by count, which
customers count, and so on. Each run makes those decisions differently.

For each question, `evidence/` shows all five runs: askdb's answer and the SQL behind it.

## Your task

Write one file, **`business_definitions.md`**: the business rules that remove the disagreement,
so that askdb answers the same way every time.

askdb reads every `.md` file in its documentation folder and treats it as the description of
the business. Your file is added to that folder.

**Write general rules, not answers.** Your file will be tested on questions you have not seen,
which depend on the same kinds of decisions on different metrics, periods, stores and channels.

Use Claude Code however you like.

## Checking your rules

You have an API key in `.env`, so askdb can run for real (`python -m askdb "..."`), on the
same model your file will be scored with. How you check
that your rules hold is up to you.

## Submission

Email your `business_definitions.md` to **tomar.ankur287@gmail.com**, with your team name in
the subject line. I will add each team's file to askdb's documentation and run a fixed set of
unseen questions several times, reporting how many askdb answers correctly, and how many it answers the same way on every run.

askdb's documentation is otherwise unchanged, so everything your rules need must be in your
file.

## Files

| File | What it is |
|---|---|
| `questions.yaml` | The ten questions |
| `evidence/NN-*.md` | Five askdb runs per question with the current docs: answer and SQL |
