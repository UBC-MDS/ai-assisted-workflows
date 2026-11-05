---
table: ErasureRequest
owner: privacy-ops
last_reviewed: 2025-10-14
---

# ErasureRequest

GDPR right-to-erasure requests, as logged by the privacy team's case system. One row per
request; a customer can have more than one.

| Column | Type | Notes |
|---|---|---|
| `RequestId` | INTEGER | Primary key |
| `CustomerId` | INTEGER | FK → `Customer.CustomerId` |
| `ReceivedDate` | DATE | When the request arrived |
| `Status` | TEXT | Current state of the request — see below |
| `StatusDate` | DATE | When it reached its current status |
| `Note` | TEXT | Free text from the privacy team, often NULL |

## Status

| Status | Meaning |
|---|---|
| `received` | Logged, identity not yet checked |
| `verified` | Identity confirmed; queued for processing |
| `completed` | Processed: personal data purged from source systems. The warehouse copy is purged in the quarterly retention job |
| `on_hold` | Cannot be processed yet: the customer's records are under a legal hold (e.g. a tax audit) |
| `rejected` | Not processed: identity could not be confirmed |
| `withdrawn` | The customer withdrew the request |

## Guidance

- Requests can come from reseller (business) accounts, made by the account's named contact.
- A customer who withdrew a request can file a new one later; use the latest request for the
  customer's current state.
