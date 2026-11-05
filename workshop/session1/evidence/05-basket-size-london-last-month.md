# Q05. What's the average basket size in London last month?

askdb was asked this question 5 times with its current documentation (model `qwen2.5-coder:14b`, docs version `sc-3d2141c2`). Each run is shown exactly as it came back.

| Run | askdb's answer |
|---|---|
| 1 | 5.969528177777777 |
| 2 | None |
| 3 | ERROR: OperationalError: no such column: i.InvoiceCount |
| 4 | ERROR: OperationalError: no such column: i.InvoiceCount |
| 5 | ERROR: OperationalError: no such column: i.InvoiceCount |

## Run 1

Answer: `5.969528177777777` (columns: AverageBasketSizeUSD)

```sql
SELECT AVG(i.Subtotal * x.RateToUSD) AS AverageBasketSizeUSD
FROM Invoice i
JOIN Store s ON s.StoreId = i.StoreId
JOIN ExchangeRate x ON x.CurrencyCode = i.CurrencyCode AND x.Month = strftime('%Y-%m', i.InvoiceDate)
WHERE i.InvoiceStatus = 'settled'
  AND s.Region = 'EU'
  AND s.Name = 'London'
  AND i.InvoiceDate >= date('2025-11-01')
  AND i.InvoiceDate < date('2025-12-01')
```

## Run 2

Answer: `None` (columns: AverageBasketSize)

```sql
WITH Invoices AS (
    SELECT i.InvoiceId, i.CustomerId, COUNT(il.InvoiceLineId) AS BasketSize
    FROM Invoice i
    JOIN Customer c ON c.CustomerId = i.CustomerId
    LEFT JOIN InvoiceLine il ON il.InvoiceId = i.InvoiceId
    JOIN Store s ON s.StoreId = i.StoreId
    WHERE c.AccountType IN ('retail', 'reseller')
      AND (s.AcquiredDate IS NULL OR c.FirstPurchaseDate >= s.AcquiredDate)
      AND s.Name = 'London'
      AND strftime('%Y-%m', i.InvoiceDate) = strftime('%Y-%m', 'now', '-1 month')
      AND i.InvoiceStatus = 'settled'
    GROUP BY i.InvoiceId, i.CustomerId
)
SELECT AVG(BasketSize) AS AverageBasketSize
FROM Invoices
```

## Run 3

Error: `OperationalError: no such column: i.InvoiceCount`

```sql
-- no SQL returned
```

## Run 4

Error: `OperationalError: no such column: i.InvoiceCount`

```sql
-- no SQL returned
```

## Run 5

Error: `OperationalError: no such column: i.InvoiceCount`

```sql
-- no SQL returned
```
