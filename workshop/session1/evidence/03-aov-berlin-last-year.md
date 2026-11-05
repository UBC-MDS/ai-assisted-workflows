# Q03. What was the average order value in Berlin last year?

askdb was asked this question 5 times with its current documentation (model `qwen2.5-coder:14b`, docs version `sc-3d2141c2`). Each run is shown exactly as it came back.

| Run | askdb's answer |
|---|---|
| 1 | 5.752686392441034 |
| 2 | 6.177569083709183 |
| 3 | 5.752686392441034 |
| 4 | 6.044322223744862 |
| 5 | 5.752686392441034 |

## Run 1

Answer: `5.752686392441034` (columns: AverageOrderValue)

```sql
WITH berlin_customers AS (
    SELECT c.CustomerId
    FROM Customer c
    JOIN Store s ON s.StoreId = c.HomeStoreId
    WHERE s.Name = 'Berlin'
      AND c.AccountType IN ('retail', 'reseller')
      AND (s.AcquiredDate IS NULL OR c.FirstPurchaseDate >= s.AcquiredDate)
), berlin_invoices AS (
    SELECT i.InvoiceId, i.Subtotal * x.RateToUSD AS SubtotalUSD
    FROM Invoice i
    JOIN ExchangeRate x ON x.CurrencyCode = i.CurrencyCode AND strftime('%Y-%m', i.InvoiceDate) = x.Month
    WHERE i.InvoiceStatus = 'settled'
      AND i.StoreId IN (SELECT StoreId FROM Store WHERE Name = 'Berlin')
      AND i.InvoiceDate >= date('2024-01-01')
      AND i.InvoiceDate < date('2025-01-01')
)
SELECT AVG(bi.SubtotalUSD) AS AverageOrderValue
FROM berlin_invoices bi;
```

## Run 2

Answer: `6.177569083709183` (columns: AvgOrderValue)

```sql
SELECT AVG(i.Subtotal * x.RateToUSD) AS AvgOrderValue
FROM Invoice i
JOIN Customer c ON c.CustomerId = i.CustomerId
JOIN Store s ON s.StoreId = i.StoreId
JOIN ExchangeRate x ON x.CurrencyCode = i.CurrencyCode AND x.Month = strftime('%Y-%m', i.InvoiceDate)
WHERE strftime('%Y', i.InvoiceDate) = '2023' AND s.Region = 'EU' AND c.AccountType NOT IN ('internal', 'test') AND (s.AcquiredDate IS NULL OR i.InvoiceDate >= s.AcquiredDate)
```

## Run 3

Answer: `5.752686392441034` (columns: AverageOrderValueUSD)

```sql
WITH BerlinInvoices AS (
    SELECT i.InvoiceId, i.Subtotal, i.CurrencyCode, strftime('%Y-%m', i.InvoiceDate) AS InvoiceMonth
    FROM Invoice i
    JOIN Store s ON s.StoreId = i.StoreId
    WHERE s.Region = 'EU'
      AND s.Name = 'Berlin'
      AND i.InvoiceStatus = 'settled'
      AND i.InvoiceDate >= date('2024-01-01')
      AND i.InvoiceDate < date('2025-01-01')
), ExchangeRates AS (
    SELECT CurrencyCode, Month, RateToUSD
    FROM ExchangeRate
)
SELECT AVG((BerlinInvoices.Subtotal * ExchangeRates.RateToUSD)) AS AverageOrderValueUSD
FROM BerlinInvoices
JOIN ExchangeRates ON ExchangeRates.CurrencyCode = BerlinInvoices.CurrencyCode AND ExchangeRates.Month = BerlinInvoices.InvoiceMonth
```

## Run 4

Answer: `6.044322223744862` (columns: AverageOrderValue)

```sql
SELECT AVG(i.Subtotal * x.RateToUSD) AS AverageOrderValue FROM Invoice i JOIN Store s ON s.StoreId = i.StoreId JOIN ExchangeRate x ON x.CurrencyCode = i.CurrencyCode AND x.Month = strftime('%Y-%m', i.InvoiceDate) WHERE s.Region = 'EU' AND strftime('%Y', i.InvoiceDate) = '2024' AND i.InvoiceStatus = 'settled'
```

## Run 5

Answer: `5.752686392441034` (columns: AverageOrderValue)

```sql
SELECT AVG(i.Subtotal * x.RateToUSD) AS AverageOrderValue
FROM Invoice i
JOIN Store s ON s.StoreId = i.StoreId
JOIN ExchangeRate x ON x.CurrencyCode = i.CurrencyCode AND x.Month = strftime('%Y-%m', i.InvoiceDate)
WHERE s.Region = 'EU' AND s.Name = 'Berlin'
AND i.InvoiceStatus = 'settled'
AND i.InvoiceDate >= date('2024-01-01') AND i.InvoiceDate < date('2025-01-01')
```
