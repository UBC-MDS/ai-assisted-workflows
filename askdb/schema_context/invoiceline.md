---
table: InvoiceLine
owner: finance
last_reviewed: 2025-08-21
---

# InvoiceLine

One row per track sold on an invoice. Local currency.

| Column | Type | Notes |
|---|---|---|
| `InvoiceLineId` | INTEGER | Primary key |
| `InvoiceId` | INTEGER | FK → `Invoice.InvoiceId` |
| `TrackId` | INTEGER | FK → `Track.TrackId` |
| `UnitPrice` | NUMERIC | Price charged, local currency |
| `Quantity` | INTEGER | Always 1 for digital tracks |
| `DiscountAmount` | NUMERIC | Line discount, local currency. Resellers get 20% on every line |

## Guidance

- Line revenue is `UnitPrice * Quantity - DiscountAmount`, in local currency.
- Use for "which tracks / genres / artists sold". For total revenue use `Invoice.Subtotal`;
  never join lines and then sum invoice-level columns (each invoice would repeat once per line).
- Refunds are recorded per invoice, not per line. For catalog revenue, ignore refunds.
