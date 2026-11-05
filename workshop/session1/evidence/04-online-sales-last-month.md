# Q04. How much did we sell online last month?

askdb was asked this question 5 times with its current documentation (model `qwen2.5-coder:14b`, docs version `sc-3d2141c2`). Each run is shown exactly as it came back.

| Run | askdb's answer |
|---|---|
| 1 | None |
| 2 | 227157.892143 |
| 3 | 5689.7259189999995 |
| 4 | None |
| 5 | None |

## Run 1

Answer: `None` (columns: SUM(mrr.NetRevenueUSD))

```sql
SELECT SUM(mrr.NetRevenueUSD) FROM MonthlyRevenueRollup mrr WHERE mrr.Channel IN ('web', 'app') AND mrr.Month = strftime('%Y-%m', 'now', '-1 month')
```

## Run 2

Answer: `227157.892143` (columns: OnlineRevenueUSD)

```sql
SELECT SUM(i.Subtotal * x.RateToUSD) AS OnlineRevenueUSD
FROM Invoice i
JOIN ExchangeRate x ON x.CurrencyCode = i.CurrencyCode AND x.Month = strftime('%Y-%m', i.InvoiceDate)
WHERE i.Channel IN ('web', 'app')
AND i.InvoiceStatus = 'settled'
```

## Run 3

Answer: `5689.7259189999995` (columns: NetRevenueUSD)

```sql
SELECT SUM(i.Subtotal * x.RateToUSD) AS NetRevenueUSD FROM Invoice i JOIN ExchangeRate x ON x.CurrencyCode = i.CurrencyCode AND x.Month = strftime('%Y-%m', i.InvoiceDate) WHERE i.Channel IN ('web', 'app') AND i.InvoiceStatus = 'settled' AND i.InvoiceDate >= date('2025-11-01') AND i.InvoiceDate < date('2025-12-01')
```

## Run 4

Answer: `None` (columns: OnlineRevenueUSD)

```sql
SELECT SUM(mrr.NetRevenueUSD) AS OnlineRevenueUSD FROM MonthlyRevenueRollup mrr WHERE mrr.Month = strftime('%Y-%m', 'now', '-1 month') AND mrr.Channel IN ('web', 'app')
```

## Run 5

Answer: `None` (columns: NetRevenueUSD)

```sql
SELECT SUM((i.Subtotal - COALESCE(rf.Refunded, 0)) * x.RateToUSD) AS NetRevenueUSD FROM Invoice i JOIN ExchangeRate x ON x.CurrencyCode = i.CurrencyCode AND x.Month = strftime('%Y-%m', i.InvoiceDate) LEFT JOIN (SELECT InvoiceId, SUM(RefundAmount) AS Refunded FROM Refund GROUP BY InvoiceId) rf ON rf.InvoiceId = i.InvoiceId WHERE i.InvoiceStatus = 'settled' AND i.Channel IN ('web', 'app') AND strftime('%Y-%m', i.InvoiceDate) = strftime('%Y-%m', 'now', '-1 month')
```
