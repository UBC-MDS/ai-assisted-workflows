---
table: FiscalMonth
owner: finance
last_reviewed: 2025-01-15
---

# FiscalMonth

Maps calendar months to the fiscal calendar.

| Column | Type | Notes |
|---|---|---|
| `Month` | TEXT | `YYYY-MM` |
| `FiscalYear` | INTEGER | Fiscal year, named for the calendar year it **ends** in |
| `FiscalQuarter` | INTEGER | 1–4 |

## Guidance

- The fiscal year starts on **1 February**. FY2025 runs Feb 2024 – Jan 2025.
- "Q1", "Q2", "this year", "last quarter" mean **fiscal** periods unless the user says
  "calendar".
- Treat **2025-12-31** as today. All data is as of that date.
