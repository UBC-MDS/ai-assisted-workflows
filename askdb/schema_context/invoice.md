---
table: Invoice
owner: finance
last_reviewed: 2025-08-21
---

# Invoice

One row per checkout. Amounts are in the **store's local currency**.

| Column | Type | Notes |
|---|---|---|
| `InvoiceId` | INTEGER | Primary key |
| `CustomerId` | INTEGER | FK → `Customer.CustomerId` |
| `StoreId` | INTEGER | FK → `Store.StoreId` |
| `InvoiceDate` | DATE | |
| `Channel` | TEXT | `web`, `app`, `store`, `reseller` |
| `CurrencyCode` | TEXT | Local currency; matches the store's currency |
| `Subtotal` | NUMERIC | Pre-tax amount after line discounts, local currency |
| `TaxAmount` | NUMERIC | Tax collected, local currency. **Never revenue** |
| `Total` | NUMERIC | `Subtotal + TaxAmount` — what the customer paid |
| `InvoiceStatus` | TEXT | `settled`, `pending` (payment not yet cleared), `void` (cancelled), `comped` (given away free) |

## Guidance

- Only `settled` invoices are revenue. `pending`, `void` and `comped` never are.
- Revenue is computed from `Subtotal`, not `Total`. Tax is a liability, not income.
- Convert to USD with `ExchangeRate` at the invoice's month before summing across stores.
- The full revenue definition, including refunds, is in `metrics.md`.
