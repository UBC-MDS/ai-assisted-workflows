# Q01. What's our order growth for last month?

askdb was asked this question 5 times with its current documentation (model `qwen2.5-coder:14b`, docs version `sc-3d2141c2`). Each run is shown exactly as it came back.

| Run | askdb's answer |
|---|---|
| 1 | 0 |
| 2 | None |
| 3 | 0 |
| 4 | -667 |
| 5 | -556 |

## Run 1

Answer: `0` (columns: OrderGrowth)

```sql
SELECT SUM(CASE WHEN i.InvoiceDate >= date('now', '-1 month') THEN 1 ELSE 0 END) - SUM(CASE WHEN i.InvoiceDate < date('now', '-2 months') AND i.InvoiceDate >= date('now', '-3 months') THEN 1 ELSE 0 END) AS OrderGrowth FROM Invoice i JOIN Customer c ON c.CustomerId = i.CustomerId JOIN Store s ON s.StoreId = i.StoreId WHERE i.InvoiceStatus = 'settled' AND c.AccountType NOT IN ('internal', 'test') AND (s.AcquiredDate IS NULL OR i.InvoiceDate >= s.AcquiredDate)
```

## Run 2

Answer: `None` (columns: LastMonthOrderGrowth)

```sql
SELECT SUM(i.InvoiceCount) AS LastMonthOrderGrowth FROM MonthlyRevenueRollup i WHERE i.Month = strftime('%Y-%m', 'now', '-1 month') AND i.AccountType IN ('retail', 'reseller');
```

## Run 3

Answer: `0` (columns: NewOrders)

```sql
SELECT SUM(CASE WHEN i.InvoiceDate >= date('now', '-1 month', 'start of month') THEN 1 ELSE 0 END) AS NewOrders FROM Invoice i INNER JOIN Customer c ON c.CustomerId = i.CustomerId INNER JOIN Store s ON s.StoreId = i.StoreId WHERE c.AccountType IN ('retail', 'reseller') AND (s.AcquiredDate IS NULL OR c.FirstPurchaseDate >= s.AcquiredDate)
```

## Run 4

Answer: `-667` (columns: OrderGrowth)

```sql
SELECT SUM(CASE WHEN strftime('%Y-%m', InvoiceDate) = strftime('%Y-%m', '2025-12-31') THEN 1 ELSE 0 END) - SUM(CASE WHEN strftime('%Y-%m', InvoiceDate) = strftime('%Y-%m', '2024-11-30') THEN 1 ELSE 0 END) AS OrderGrowth FROM Invoice WHERE InvoiceStatus = 'settled';
```

## Run 5

Answer: `-556` (columns: OrderGrowth)

```sql
SELECT SUM(CASE WHEN strftime('%Y-%m', InvoiceDate) = '2025-10' THEN Quantity ELSE 0 END) - SUM(CASE WHEN strftime('%Y-%m', InvoiceDate) = '2025-09' THEN Quantity ELSE 0 END) AS OrderGrowth FROM InvoiceLine JOIN Invoice ON Invoice.InvoiceId = InvoiceLine.InvoiceId WHERE Invoice.InvoiceStatus = 'settled';
```
