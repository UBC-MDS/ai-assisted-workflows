# Q10. How much subscription revenue did we book in 2025?

askdb was asked this question 5 times with its current documentation (model `qwen2.5-coder:14b`, docs version `sc-3d2141c2`). Each run is shown exactly as it came back.

| Run | askdb's answer |
|---|---|
| 1 | 17416135.05 |
| 2 | 3595080411.395 |
| 3 | ERROR: OperationalError: no such column: P.MonthlyPriceUSD |
| 4 | ERROR: OperationalError: no such function: DATEDIFF |
| 5 | 32862276192.565 |

## Run 1

Answer: `17416135.05` (columns: SubscriptionRevenueUSD)

```sql
SELECT SUM(p.MonthlyPriceUSD * f.FiscalYear) AS SubscriptionRevenueUSD FROM Subscription s JOIN Plan p ON s.PlanId = p.PlanId JOIN FiscalMonth f ON strftime('%Y-%m', s.StartDate) = f.Month WHERE f.FiscalYear >= 2025 AND (s.EndDate IS NULL OR strftime('%Y-%m', s.EndDate) >= '2024-12-31')
```

## Run 2

Answer: `3595080411.395` (columns: SubscriptionRevenueUSD)

```sql
SELECT SUM(p.MonthlyPriceUSD * julianday(s.EndDate) - julianday(s.StartDate)) AS SubscriptionRevenueUSD FROM Subscription s JOIN Plan p ON p.PlanId = s.PlanId WHERE strftime('%Y', s.StartDate) = '2025' AND (s.EndDate IS NULL OR strftime('%Y', s.EndDate) >= '2025')
```

## Run 3

Error: `OperationalError: no such column: P.MonthlyPriceUSD`

```sql
-- no SQL returned
```

## Run 4

Error: `OperationalError: no such function: DATEDIFF`

```sql
-- no SQL returned
```

## Run 5

Answer: `32862276192.565` (columns: SubscriptionRevenueUSD)

```sql
SELECT SUM(p.MonthlyPriceUSD * julianday('2025-12-31') - julianday(s.StartDate) + 1) AS SubscriptionRevenueUSD FROM Subscription s JOIN Plan p ON p.PlanId = s.PlanId WHERE (s.EndDate IS NULL OR s.EndDate >= '2025-01-01') AND s.StartDate <= '2025-12-31'
```
