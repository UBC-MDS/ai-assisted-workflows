---
table: Store
owner: data-platform
last_reviewed: 2025-06-02
---

# Store

Six stores. Every invoice is booked to the customer's home store, in that store's currency.

| Column | Type | Notes |
|---|---|---|
| `StoreId` | INTEGER | Primary key |
| `Name` | TEXT | Toronto, New York, London, Berlin, São Paulo, Sydney |
| `Region` | TEXT | `NA`, `EU`, `LATAM`, `APAC` |
| `Country` | TEXT | |
| `CurrencyCode` | TEXT | Invoice currency for this store: CAD, USD, GBP, EUR, BRL, AUD |
| `TaxRate` | NUMERIC | Sales tax / VAT rate applied at checkout |
| `OpenedDate` | DATE | |
| `AcquiredDate` | DATE | Set only for stores we acquired rather than opened. São Paulo: 2023-07-01 |

## Guidance

- For revenue or customers "by region" or "by store", group on `Store.Region` / `Store.Name`
  via the customer's `HomeStoreId`.
- See `customer_population.md` for how `AcquiredDate` affects reporting.
