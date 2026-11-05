---
table: MonthlyRevenueRollup
owner: data-platform
last_reviewed: 2025-03-10
---

# MonthlyRevenueRollup

Pre-aggregated net product revenue, refreshed nightly by the data-platform ETL.

| Column | Type | Notes |
|---|---|---|
| `Month` | TEXT | `YYYY-MM` of the invoice |
| `StoreId` | INTEGER | FK → `Store.StoreId` |
| `Channel` | TEXT | `web`, `app`, `store`, `reseller` |
| `AccountType` | TEXT | `retail` or `reseller` |
| `NetRevenueUSD` | NUMERIC | Net product revenue in USD — the revenue definition in `metrics.md`, already applied |
| `InvoiceCount` | INTEGER | Settled invoices |

## Guidance

- **Revenue questions covering six months or more must use this table**, not the raw
  invoice tables. The raw join is too slow at that range.
- For shorter windows, compute from `Invoice` as described in `metrics.md`.
- `NetRevenueUSD` is final — finance's revenue definition already applied. Do not re-apply
  exchange rates, refunds or account filters.
