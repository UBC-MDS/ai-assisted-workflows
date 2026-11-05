---
table: Refund
owner: finance
last_reviewed: 2025-08-21
---

# Refund

Refunds issued against settled invoices. Some are partial.

| Column | Type | Notes |
|---|---|---|
| `RefundId` | INTEGER | Primary key |
| `InvoiceId` | INTEGER | FK → `Invoice.InvoiceId` |
| `RefundDate` | DATE | When the refund was issued |
| `RefundAmount` | NUMERIC | Tax-exclusive amount refunded, in the invoice's local currency |
| `Reason` | TEXT | Free text category |

## Guidance

- An invoice can have more than one refund. Sum per invoice before joining.
- Refunds reduce revenue **in the month of the original invoice**, at that month's exchange
  rate — not in the month the refund was issued.
