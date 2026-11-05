# Q06. How much did we discount in Q3?

askdb was asked this question 5 times with its current documentation (model `qwen2.5-coder:14b`, docs version `sc-3d2141c2`). Each run is shown exactly as it came back.

| Run | askdb's answer |
|---|---|
| 1 | 18683.45 |
| 2 | 2735.492675 |
| 3 | 12393.428462 |
| 4 | ERROR: OperationalError: no such column: c.AccountType |
| 5 | ERROR: OperationalError: no such column: rf.Refunded |

## Run 1

Answer: `18683.45` (columns: TotalDiscounts)

```sql
SELECT SUM(DiscountAmount) AS TotalDiscounts FROM InvoiceLine INNER JOIN Invoice ON InvoiceLine.InvoiceId = Invoice.InvoiceId INNER JOIN FiscalMonth ON strftime('%Y-%m', Invoice.InvoiceDate) = FiscalMonth.Month WHERE FiscalMonth.FiscalQuarter = 3 AND Invoice.InvoiceStatus = 'settled';
```

## Run 2

Answer: `2735.492675` (columns: TotalDiscountsUSD)

```sql
SELECT SUM(il.DiscountAmount * x.RateToUSD) AS TotalDiscountsUSD FROM InvoiceLine il JOIN Invoice i ON il.InvoiceId = i.InvoiceId JOIN ExchangeRate x ON x.CurrencyCode = i.CurrencyCode AND x.Month = strftime('%Y-%m', i.InvoiceDate) WHERE i.InvoiceStatus = 'settled' AND strftime('%Y-%m', i.InvoiceDate) BETWEEN '2023-07' AND '2023-09';
```

## Run 3

Answer: `12393.428462` (columns: TotalDiscountsUSD)

```sql
SELECT SUM(il.DiscountAmount * x.RateToUSD) AS TotalDiscountsUSD
FROM InvoiceLine il
JOIN Invoice i ON il.InvoiceId = i.InvoiceId
JOIN ExchangeRate x ON x.CurrencyCode = i.CurrencyCode AND strftime('%Y-%m', i.InvoiceDate) = x.Month
WHERE i.InvoiceStatus = 'settled' AND strftime('%m', i.InvoiceDate) BETWEEN '07' AND '09'
```

## Run 4

Error: `OperationalError: no such column: c.AccountType`

```sql
-- no SQL returned
```

## Run 5

Error: `OperationalError: no such column: rf.Refunded`

```sql
-- no SQL returned
```
