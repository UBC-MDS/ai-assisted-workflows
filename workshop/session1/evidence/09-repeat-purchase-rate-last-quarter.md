# Q09. What was the repeat purchase rate last quarter?

askdb was asked this question 5 times with its current documentation (model `qwen2.5-coder:14b`, docs version `sc-3d2141c2`). Each run is shown exactly as it came back.

| Run | askdb's answer |
|---|---|
| 1 | 53.91634980988593 |
| 2 | ERROR: OperationalError: misuse of aggregate function COUNT() |
| 3 | None |
| 4 | ERROR: OperationalError: no such column: f.FiscalMonth |
| 5 | 1.0 |

## Run 1

Answer: `53.91634980988593` (columns: RepeatPurchaseRate)

```sql
WITH LastQuarterCustomers AS (
    SELECT DISTINCT c.CustomerId
    FROM Customer c
    JOIN Invoice i ON c.CustomerId = i.CustomerId
    WHERE strftime('%Y-%m', i.InvoiceDate) IN (
        SELECT fm.Month
        FROM FiscalMonth fm
        WHERE fm.FiscalYear = 2025 AND fm.FiscalQuarter = 3
    )
), RepeatPurchaseCustomers AS (
    SELECT DISTINCT c.CustomerId
    FROM LastQuarterCustomers c
    JOIN Invoice i ON c.CustomerId = i.CustomerId
    WHERE strftime('%Y-%m', i.InvoiceDate) IN (
        SELECT fm.Month
        FROM FiscalMonth fm
        WHERE fm.FiscalYear = 2024 AND fm.FiscalQuarter = 4
    )
)
SELECT CAST(COUNT(DISTINCT RepeatPurchaseCustomers.CustomerId) AS REAL) * 100 / COUNT(DISTINCT LastQuarterCustomers.CustomerId) AS RepeatPurchaseRate
FROM LastQuarterCustomers
LEFT JOIN RepeatPurchaseCustomers ON LastQuarterCustomers.CustomerId = RepeatPurchaseCustomers.CustomerId;
```

## Run 2

Error: `OperationalError: misuse of aggregate function COUNT()`

```sql
-- no SQL returned
```

## Run 3

Answer: `None` (columns: RepeatPurchaseRate)

```sql
WITH CustomerPurchases AS (
    SELECT c.CustomerId, MIN(i.InvoiceDate) AS FirstPurchaseDate, COUNT(DISTINCT i.InvoiceDate) AS PurchaseCount
    FROM Customer c
    JOIN Invoice i ON c.CustomerId = i.CustomerId
    WHERE i.InvoiceStatus = 'settled'
      AND c.AccountType IN ('retail', 'reseller')
    GROUP BY c.CustomerId
),
RecentCustomers AS (
    SELECT CustomerId, FirstPurchaseDate, PurchaseCount
    FROM CustomerPurchases
    WHERE FirstPurchaseDate >= DATE('now', '-3 months', '+1 day')
)
SELECT SUM(CASE WHEN PurchaseCount > 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS RepeatPurchaseRate
FROM RecentCustomers;
```

## Run 4

Error: `OperationalError: no such column: f.FiscalMonth`

```sql
-- no SQL returned
```

## Run 5

Answer: `1.0` (columns: RepeatPurchaseRate)

```sql
SELECT AVG(c.LastActiveDate >= date(c.FirstPurchaseDate, '+3 months')) AS RepeatPurchaseRate FROM Customer c WHERE strftime('%Y-%m', c.LastActiveDate) = '2025-10' AND strftime('%Y-%m', c.FirstPurchaseDate) IN ('2024-07', '2024-08', '2024-09') AND c.AccountType NOT IN ('internal', 'test')
```
