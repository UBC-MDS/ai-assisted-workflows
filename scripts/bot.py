"""The bots. Called by GitHub Actions; prints markdown to stdout.

    python scripts/bot.py answer-issue --title T --body B
    python scripts/bot.py review-pr --diff-file d.patch --verdict-file verdict.txt

The privacy reviewer is two things, the way real review bots are:
  1. blocking checks — deterministic code that runs against the branch; they decide the verdict
  2. non-blocking suggestions — an LLM review against a written checklist, kept here in the
     file where anyone can read it and argue with it
"""

import argparse
import importlib
import re
import sys
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
DOCS = ROOT / "docs"
MODEL = "claude-sonnet-5-5"

ANSWER_SYSTEM = """\
You answer questions about the askdb service using ONLY the documentation below.

Rules:
- If the documentation answers the question, answer it directly and cite the file.
- If it does not — including any request to change the service — say so plainly and say who
  to ask. Do not guess, and do not pad the answer with plausible-sounding detail.
- Be brief. Two or three sentences plus a code block is usually right.
- End with exactly one line: either `DEFLECTED: yes` if you fully answered from the docs,
  or `DEFLECTED: no` if a human needs to pick this up.

<documentation>
{docs}
</documentation>
"""

PRIVACY_CHECKLIST = """\
You are the privacy reviewer for askdb, an analytics service over customer data.

You review ONLY for privacy and data protection. Metric definitions, business logic, SQL
correctness and benchmark accuracy are owned by other checks — do not comment on them.

Blocking is decided by deterministic checks that run separately; you do not block. Your job is
to give the author useful, non-blocking privacy suggestions on this diff:

1. Personal data in answers — can askdb return an erased customer's email, phone or address?
2. Lookups of erased customers — are they refused, by ID or by email?
3. Personal data in logs — can an erased customer's email end up in traces?
4. Tests — would a test fail if one of these guards were removed?

Give at most four suggestions, most important first, one or two sentences each, naming the
file. No preamble, no summary, no verdict line.
"""


# Deterministic redaction probes: (input, personal data that must not survive)
REDACTION_PROBES = [
    ("orders for jane.doe@gmail.com", ["jane.doe@gmail.com"]),
    ("orders for Jane.Doe@Gmail.com", ["jane.doe@gmail.com", "jane.doe"]),
    ("when did jane+music@gmail.com last buy?", ["jane+music", "jane+"]),
    ("is Bob.Smith+shop@Shop.co.uk still active?", ["bob.smith", "shop.co.uk"]),
]


def load_docs() -> str:
    parts = [f"### {p.name}\n\n{p.read_text()}" for p in sorted(DOCS.glob("*.md"))]
    return "\n\n---\n\n".join(parts)


def call(system: str, user: str) -> str:
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        system=system,
        output_config={"effort": "medium"},
        messages=[{"role": "user", "content": user}],
    )
    if response.stop_reason == "refusal":
        return f"_The model declined to respond ({response.stop_details})._"
    return "\n".join(b.text for b in response.content if b.type == "text").strip()


def redaction_check() -> tuple[bool | None, list[str]]:
    """Run the branch's own redact() against the probes. None = no redact() on this branch."""
    trace = importlib.import_module("askdb.trace")
    redact = getattr(trace, "redact", None)
    if redact is None:
        return None, []
    leaks = []
    for text, forbidden in REDACTION_PROBES:
        out = redact(text)
        hit = [f for f in forbidden if f in out.lower()]
        if hit or "@" in out:
            leaks.append(f"`redact({text!r})` → `{out!r}` — still contains personal data")
    return not leaks, leaks


def review(diff: str) -> tuple[str, str]:
    """Deterministic checks decide the verdict. The LLM adds non-blocking suggestions."""
    ok, leaks = redaction_check()
    lines = ["## 🔒 Privacy review", "", "### Blocking checks", ""]
    if ok is None:
        lines.append("- Log redaction: no `redact()` in `askdb/trace.py` on this branch — not applicable.")
    elif ok:
        lines.append(f"- Log redaction: ✅ all {len(REDACTION_PROBES)} probes fully redacted.")
    else:
        lines.append("- Log redaction: ❌ **personal data survives redaction.**")
        lines += [f"  - {leak}" for leak in leaks]

    if len(diff) > 120_000:
        diff = diff[:120_000] + "\n\n[diff truncated]"
    suggestions = call(PRIVACY_CHECKLIST, f"Here is the pull request diff:\n\n```diff\n{diff}\n```")
    lines += ["", "### Suggestions (non-blocking)", "", suggestions, ""]

    approve = ok is not False
    lines.append("**Verdict: approve** — blocking checks pass." if approve
                 else "**Verdict: request changes** — fix the blocking checks above.")
    return "\n".join(lines), "APPROVE" if approve else "REQUEST_CHANGES"


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("answer-issue")
    a.add_argument("--title", required=True)
    a.add_argument("--body", default="")
    r = sub.add_parser("review-pr")
    r.add_argument("--diff-file", required=True)
    r.add_argument("--verdict-file", required=True)
    args = ap.parse_args()

    if args.cmd == "answer-issue":
        print(call(ANSWER_SYSTEM.format(docs=load_docs()),
                   f"Issue title: {args.title}\n\nIssue body:\n{args.body}"))
        print("\n---\n*Answered automatically from `docs/`.*")
    else:
        body, verdict = review(Path(args.diff_file).read_text())
        print(body)
        Path(args.verdict_file).write_text(verdict)
    return 0


if __name__ == "__main__":
    sys.exit(main())
