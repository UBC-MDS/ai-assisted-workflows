---
table: Subscription, Plan
owner: crm
last_reviewed: 2025-09-18
---

# Subscription and Plan

Streaming subscriptions — a separate revenue stream from track sales.

**Plan**

| Column | Type | Notes |
|---|---|---|
| `PlanId` | INTEGER | Primary key |
| `Name` | TEXT | Basic, Premium, Family |
| `MonthlyPriceUSD` | NUMERIC | Billed monthly, in USD |

**Subscription**

| Column | Type | Notes |
|---|---|---|
| `SubscriptionId` | INTEGER | Primary key |
| `CustomerId` | INTEGER | FK → `Customer.CustomerId` |
| `PlanId` | INTEGER | FK → `Plan.PlanId` |
| `StartDate` | DATE | |
| `EndDate` | DATE | NULL while active |

## Guidance

- Subscription revenue is recognised monthly: `MonthlyPriceUSD` for each month the
  subscription is active.
- "Revenue" on its own means **product revenue** (track sales). Say "subscription revenue"
  or "total revenue" (product + subscription) explicitly.
