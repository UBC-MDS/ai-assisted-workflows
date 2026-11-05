---
standard: SEC-2291 — Email redaction in logs
owner: Security (security@chinook-music.com)
status: approved
last_reviewed: 2025-06-12
---

# SEC-2291 — Email redaction in logs

Any service that writes user-entered text to logs must redact email addresses first, using the
pattern and helper below. **Use them verbatim.** Changes to the pattern go through Security
review; do not modify it in a service.

```python
# Security-approved pattern (SEC-2291). Use verbatim.
EMAIL_PATTERN = re.compile(r"[a-z0-9._%-]+@[a-z0-9.-]+\.[a-z]{2,}")


def redact(text: str) -> str:
    return EMAIL_PATTERN.sub("[REDACTED]", text)
```

## Required tests

Every service adopting SEC-2291 must include these tests unchanged:

```python
import unittest

from askdb.trace import redact


class TestRedact(unittest.TestCase):
    def test_email_is_redacted(self):
        self.assertEqual(redact("orders for jane.doe@gmail.com"), "orders for [REDACTED]")

    def test_email_with_subdomain_is_redacted(self):
        self.assertEqual(redact("is bob@shop.co.uk still active?"), "is [REDACTED] still active?")

    def test_text_without_email_is_unchanged(self):
        self.assertEqual(redact("no email here"), "no email here")
```

For askdb, the helper belongs in `askdb/trace.py` and the tests in `tests/test_redact.py`.
