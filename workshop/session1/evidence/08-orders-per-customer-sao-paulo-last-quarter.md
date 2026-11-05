# Q08. How many orders per customer did São Paulo customers place last quarter?

askdb was asked this question 5 times with its current documentation (model `qwen2.5-coder:14b`, docs version `sc-3d2141c2`). Each run is shown exactly as it came back.

| Run | askdb's answer |
|---|---|
| 1 | [[1], [3], [4], [1], [1]] … |
| 2 | 889 |
| 3 | [[5, 1], [6, 4], [9, 3], [22, 2], [42, 1]] … |
| 4 | 2.532763532763533 |
| 5 | 889 |

## Run 1

Answer: `[[1], [3], [4], [1], [1]]` (columns: OrdersPerCustomer)

```sql
SELECT COUNT(DISTINCT i.InvoiceId) AS OrdersPerCustomer
FROM Invoice i
JOIN Customer c ON c.CustomerId = i.CustomerId
JOIN Store s ON s.StoreId = c.HomeStoreId
WHERE s.Name = 'São Paulo'
AND strftime('%Y-%m', i.InvoiceDate) IN (
    SELECT Month FROM FiscalMonth WHERE FiscalQuarter = 4 AND FiscalYear = 2024
)
GROUP BY c.CustomerId
```

## Run 2

Answer: `889` (columns: OrdersPerCustomer)

```sql
SELECT COUNT(DISTINCT i.InvoiceId) AS OrdersPerCustomer FROM Customer c JOIN Invoice i ON c.CustomerId = i.CustomerId JOIN Store s ON s.StoreId = i.StoreId WHERE s.Name = 'São Paulo' AND i.InvoiceDate >= date('2024-10-01') AND i.InvoiceDate < date('2025-01-01');
```

## Run 3

Answer: `[[5, 1], [6, 4], [9, 3], [22, 2], [42, 1]]` (columns: CustomerId, OrderCount)

```sql
SELECT c.CustomerId, COUNT(i.InvoiceId) AS OrderCount FROM Customer c JOIN Store s ON s.StoreId = c.HomeStoreId JOIN Invoice i ON i.CustomerId = c.CustomerId WHERE s.Name = 'São Paulo' AND i.InvoiceDate BETWEEN '2024-10-01' AND '2024-12-31' GROUP BY c.CustomerId
```

## Run 4

Answer: `2.532763532763533` (columns: AvgOrdersPerCustomer)

```sql
WITH SalesOrders AS (
  SELECT COUNT(*) AS OrderCount, i.CustomerId
  FROM Invoice i
  JOIN Customer c ON c.CustomerId = i.CustomerId
  JOIN Store s ON s.StoreId = c.HomeStoreId
  WHERE s.Name = 'São Paulo'
    AND i.InvoiceDate >= date('2024-10-01')
    AND i.InvoiceDate < date('2025-01-01')
  GROUP BY i.CustomerId
)
SELECT AVG(OrderCount) AS AvgOrdersPerCustomer
FROM SalesOrders;
```

## Run 5

Answer: `889` (columns: NumberOfOrders)

```sql
SELECT COUNT(*) AS NumberOfOrders FROM Invoice i JOIN Customer c ON i.CustomerId = c.CustomerId JOIN Store s ON c.HomeStoreId = s.StoreId WHERE s.Name = 'São Paulo' AND i.InvoiceDate >= '2024-10-01' AND i.InvoiceDate < '2025-01-01'
```
