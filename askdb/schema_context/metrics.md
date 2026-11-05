---
doc: metrics
owner: analytics
last_reviewed: 2025-11-04
---

# Metric definitions

The canonical definitions. If a question uses one of these words, use the definition here.

## Revenue (net product revenue, USD)

Revenue is owned by finance. **It is not restricted to the customer population** — every
paying account counts, except internal and test accounts. Sales made by the São Paulo store
before its acquisition (2023-07-01) were the previous owner's revenue and are excluded.

Settled invoices, tax-exclusive, net of refunds, converted at the invoice month's rate:

```sql
SUM((i.Subtotal - COALESCE(rf.Refunded, 0)) * x.RateToUSD)
-- rf: (SELECT InvoiceId, SUM(RefundAmount) AS Refunded FROM Refund GROUP BY InvoiceId)
-- x:  ExchangeRate on currency and strftime('%Y-%m', i.InvoiceDate)
-- s:  Store on s.StoreId = i.StoreId;  c: Customer on c.CustomerId = i.CustomerId
WHERE i.InvoiceStatus = 'settled'
  AND c.AccountType NOT IN ('internal', 'test')
  AND (s.AcquiredDate IS NULL OR i.InvoiceDate >= s.AcquiredDate)
```

**Six months or more:** use `MonthlyRevenueRollup` instead (see that doc).

## Customer metrics

Everything below is restricted to the customer population in `customer_population.md`.

## 12-month retention

For a cohort (customers grouped by `FirstPurchaseDate`), the share still active 12 months
after their first purchase:

```sql
AVG(c.LastActiveDate >= date(c.FirstPurchaseDate, '+12 months'))
```

Only cohorts with `FirstPurchaseDate <= '2024-12-31'` are complete. Report as a percentage,
one decimal place.

## 12-month churn

`100 - 12-month retention`, same cohorts.

## Active customers

Customers in the population with `LastActiveDate >= '2025-10-02'` (active in the last 90 days).

## Customer count

Customers in the population. "How many customers do we have" means all of them, ever.

## ARPU

Revenue for a period (finance definition above) divided by the number of population
customers with a settled invoice in that period.

## LTV

Total revenue to date (finance definition) per population customer, averaged over a cohort.

## Formatting

Money in USD, two decimals. Percentages with one decimal.
