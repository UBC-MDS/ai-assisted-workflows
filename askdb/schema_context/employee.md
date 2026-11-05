---
table: Employee
owner: people-ops
last_reviewed: 2024-11-30
---

# Employee

| Column | Type | Notes |
|---|---|---|
| `EmployeeId` | INTEGER | Primary key |
| `FirstName`, `LastName` | TEXT | |
| `Title` | TEXT | Sales Support Agents are the support reps |
| `ReportsTo` | INTEGER | FK → `Employee.EmployeeId` |
| `Email` | TEXT | |

## Guidance

- `Customer.SupportRepId` points here. Only Sales Support Agents have customers.
