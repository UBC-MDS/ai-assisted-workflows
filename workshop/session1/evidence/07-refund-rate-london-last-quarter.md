# Q07. What was London's refund rate last quarter?

askdb was asked this question 5 times with its current documentation (model `qwen2.5-coder:14b`, docs version `sc-3d2141c2`). Each run is shown exactly as it came back.

| Run | askdb's answer |
|---|---|
| 1 | 4.398148148148148 |
| 2 | 0.03934871099050204 |
| 3 | 0.03214400655024537 |
| 4 | 0.9162011173184358 |
| 5 | 3.809794245818888e-05 |

## Run 1

Answer: `4.398148148148148` (columns: RefundRate)

```sql
SELECT SUM(CASE WHEN r.RefundAmount IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS RefundRate FROM Invoice i LEFT JOIN Refund r ON i.InvoiceId = r.InvoiceId INNER JOIN Store s ON i.StoreId = s.StoreId WHERE s.Name = 'London' AND strftime('%Y-%m', i.InvoiceDate) BETWEEN '2024-10-01' AND '2024-12-31';
```

## Run 2

Answer: `0.03934871099050204` (columns: RefundRate)

```sql
SELECT SUM(CASE WHEN r.InvoiceId IS NOT NULL THEN 1 ELSE 0 END) * 1.0 / COUNT(i.InvoiceId) AS RefundRate FROM Invoice i LEFT JOIN Refund r ON i.InvoiceId = r.InvoiceId INNER JOIN Store s ON i.StoreId = s.StoreId WHERE s.Name = 'London' AND strftime('%Y-%m', i.InvoiceDate) BETWEEN '2025-10-01' AND '2025-12-31'
```

## Run 3

Answer: `0.03214400655024537` (columns: RefundRate)

```sql
WITH RefundSummary AS (
    SELECT
        i.StoreId,
        SUM(rf.RefundAmount * x.RateToUSD) / SUM(i.Subtotal * x.RateToUSD) AS RefundRate
    FROM
        Invoice i
    LEFT JOIN
        Refund rf ON rf.InvoiceId = i.InvoiceId
    JOIN
        ExchangeRate x ON x.CurrencyCode = i.CurrencyCode AND x.Month = strftime('%Y-%m', i.InvoiceDate)
    WHERE
        i.InvoiceStatus = 'settled'
        AND i.StoreId = (SELECT StoreId FROM Store WHERE Name = 'London')
        AND i.InvoiceDate >= date('2025-09-01') AND i.InvoiceDate < date('2025-12-01')
    GROUP BY
        i.StoreId
)
SELECT RefundRate FROM RefundSummary;
```

## Run 4

Answer: `0.9162011173184358` (columns: RefundRate)

```sql
SELECT SUM(CASE WHEN i.InvoiceStatus = 'settled' THEN 1 ELSE 0 END) * 1.0 / COUNT(i.InvoiceId) AS RefundRate
FROM Invoice i
JOIN Customer c ON c.CustomerId = i.CustomerId
JOIN Store s ON s.StoreId = c.HomeStoreId
LEFT JOIN Refund rf ON rf.InvoiceId = i.InvoiceId
WHERE strftime('%Y-%m', i.InvoiceDate) IN ('2025-10', '2025-11', '2025-12')
AND s.Name = 'London'
AND c.AccountType NOT IN ('internal', 'test')
AND (s.AcquiredDate IS NULL OR i.InvoiceDate >= s.AcquiredDate)
```

## Run 5

Answer: `3.809794245818888e-05` (columns: RefundRate)

```sql
WITH RefundSummary AS (
    SELECT i.StoreId, COUNT(DISTINCT i.InvoiceId) AS TotalInvoices, SUM(r.RefundAmount * x.RateToUSD) / 100 AS TotalRefunds
    FROM Invoice i
    JOIN Store s ON s.StoreId = i.StoreId
    LEFT JOIN Refund r ON r.InvoiceId = i.InvoiceId
    JOIN ExchangeRate x ON x.CurrencyCode = i.CurrencyCode AND x.Month = strftime('%Y-%m', i.InvoiceDate)
    WHERE i.InvoiceStatus = 'settled'
      AND s.Name = 'London'
      AND i.InvoiceDate >= date('2025-10-01')
      AND i.InvoiceDate < date('2025-12-01')
    GROUP BY i.StoreId
)
SELECT CASE WHEN TotalInvoices > 0 THEN (TotalRefunds / (TotalInvoices * SUM(i.Subtotal) * x.RateToUSD / 100)) ELSE 0 END AS RefundRate
FROM RefundSummary rs
JOIN Invoice i ON i.StoreId = rs.StoreId
JOIN ExchangeRate x ON x.CurrencyCode = i.CurrencyCode AND x.Month = strftime('%Y-%m', i.InvoiceDate)
WHERE i.InvoiceStatus = 'settled'
  AND i.InvoiceDate >= date('2025-10-01')
  AND i.InvoiceDate < date('2025-12-01');
```
