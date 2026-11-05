# Q02. How many orders did we take in the last two weeks?

askdb was asked this question 5 times with its current documentation (model `qwen2.5-coder:14b`, docs version `sc-3d2141c2`). Each run is shown exactly as it came back.

| Run | askdb's answer |
|---|---|
| 1 | 0 |
| 2 | 0 |
| 3 | 0 |
| 4 | 605 |
| 5 | 0 |

## Run 1

Answer: `0` (columns: COUNT(*))

```sql
SELECT COUNT(*) FROM Invoice WHERE InvoiceDate >= date('now','-14 days') AND InvoiceStatus = 'settled';
```

## Run 2

Answer: `0` (columns: OrderCount)

```sql
SELECT COUNT(*) AS OrderCount FROM Invoice WHERE InvoiceDate >= date('now', '-14 days')
```

## Run 3

Answer: `0` (columns: TotalOrders)

```sql
SELECT COUNT(*) AS TotalOrders FROM Invoice WHERE InvoiceDate >= date('now', '-14 days') AND InvoiceStatus = 'settled';
```

## Run 4

Answer: `605` (columns: COUNT(*))

```sql
SELECT COUNT(*) FROM Invoice WHERE InvoiceDate >= date('2025-12-31', '-14 days') AND InvoiceStatus = 'settled';
```

## Run 5

Answer: `0` (columns: COUNT(*))

```sql
SELECT COUNT(*) FROM Invoice WHERE InvoiceDate >= date('2025-12-31', '-2 weeks') AND InvoiceStatus = 'settled';
```
