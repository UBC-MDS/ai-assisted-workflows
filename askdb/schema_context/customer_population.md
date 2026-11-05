---
doc: customer_population
owner: analytics
last_reviewed: 2025-11-04
---

# Customer population

**The customer population used by all customer-level metrics** — customer counts, customer
lists and top-N customers, retention, churn, active customers, ARPU and LTV. Any query that
counts, lists or segments customers must restrict to this population.

Revenue is a finance definition and does not use this population — see `metrics.md`.

Defined once, here, so every metric agrees on who a customer is.

## Rules

- **Real accounts only.** `internal` (staff purchases) and `test` (QA) accounts are excluded.
- **Acquired-store history excluded.** The São Paulo store was acquired on 2023-07-01.
  Customers whose first purchase there predates the acquisition belong to the previous
  owner's book of business and are not ours to report on.

## Canonical filter

Alias `Customer` as `c` and join `Store` as `s` on `s.StoreId = c.HomeStoreId`, then apply:

```sql
c.AccountType IN ('retail', 'reseller')
AND (s.AcquiredDate IS NULL OR c.FirstPurchaseDate >= s.AcquiredDate)
```

Use this filter verbatim. Do not re-derive it per metric.
