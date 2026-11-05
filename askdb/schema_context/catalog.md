---
table: Track, Album, Artist, Genre, MediaType
owner: catalog
last_reviewed: 2025-05-27
---

# Catalogue

The music catalogue.

| Table | Key columns |
|---|---|
| `Track` | `TrackId`, `Name`, `AlbumId`, `GenreId`, `MediaTypeId`, `Composer`, `Milliseconds`, `UnitPriceUSD` (list price) |
| `Album` | `AlbumId`, `Title`, `ArtistId` |
| `Artist` | `ArtistId`, `Name` |
| `Genre` | `GenreId`, `Name` |
| `MediaType` | `MediaTypeId`, `Name` |

## Guidance

- `Track.UnitPriceUSD` is the list price. What a customer actually paid is on
  `InvoiceLine`, in local currency.
- `Track.AlbumId` and `Track.GenreId` can be NULL.
- **Units sold** count every line on a `settled` invoice, from every account — royalties are
  owed on all of them, so no account or customer filters apply. Units = `SUM(Quantity)`.
