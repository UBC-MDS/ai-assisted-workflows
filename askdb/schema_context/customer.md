---
table: Customer
owner: crm
last_reviewed: 2025-09-18
---

# Customer

One row per customer account. Who counts as a customer for reporting is defined in
`customer_population.md`, not here.

| Column | Type | Notes |
|---|---|---|
| `CustomerId` | INTEGER | Primary key |
| `FirstName`, `LastName` | TEXT | |
| `Email` | TEXT | Contact email |
| `Phone`, `Address`, `City` | TEXT | |
| `Country` | TEXT | Country of the customer's home store |
| `AccountType` | TEXT | `retail`, `reseller` (B2B, wholesale pricing), `internal` (staff), `test` (QA) |
| `HomeStoreId` | INTEGER | FK → `Store.StoreId`. All of a customer's invoices are booked to this store |
| `SupportRepId` | INTEGER | FK → `Employee.EmployeeId` |
| `FirstPurchaseDate` | DATE | Date of first invoice. **Defines the customer's cohort** |
| `LastActiveDate` | DATE | Most recent purchase or active subscription day, maintained nightly by the CRM ETL. Equals `2025-12-31` for customers active today |

## Guidance

- Cohorts are monthly or yearly by `FirstPurchaseDate`.
- Use `Country` or `HomeStoreId` for geography, never the invoice's billing details.
- GDPR erasure requests are recorded separately, in `ErasureRequest` (see `erasure_request.md`).
