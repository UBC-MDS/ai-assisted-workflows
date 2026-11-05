---
table: ExchangeRate
owner: finance
last_reviewed: 2025-01-15
---

# ExchangeRate

Monthly average rates. One row per currency per month.

| Column | Type | Notes |
|---|---|---|
| `CurrencyCode` | TEXT | CAD, USD, GBP, EUR, BRL, AUD |
| `Month` | TEXT | `YYYY-MM` |
| `RateToUSD` | NUMERIC | Multiply a local amount by this to get USD. USD rows are 1.0 |

## Guidance

- All reported money is USD. Join on currency **and** the invoice's month:
  `x.CurrencyCode = i.CurrencyCode AND x.Month = strftime('%Y-%m', i.InvoiceDate)`.
