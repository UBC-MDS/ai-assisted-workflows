"""Rebuild MonthlyRevenueRollup — the data-platform ETL, run nightly in production.

Net product revenue in USD by finance's definition (askdb/schema_context/metrics.md):
settled invoices, tax-exclusive, net of refunds, converted at the invoice month's rate,
internal and test accounts excluded, São Paulo sales before the acquisition excluded.

    python scripts/rebuild_rollup.py
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "askdb.sqlite"

ROLLUP_SQL = """
INSERT INTO MonthlyRevenueRollup
SELECT strftime('%Y-%m', i.InvoiceDate), i.StoreId, i.Channel, c.AccountType,
       ROUND(SUM((i.Subtotal - COALESCE(r.Refunded, 0)) * x.RateToUSD), 2),
       COUNT(*)
FROM Invoice i
JOIN Customer c ON c.CustomerId = i.CustomerId
JOIN Store s ON s.StoreId = i.StoreId
JOIN ExchangeRate x ON x.CurrencyCode = i.CurrencyCode
                   AND x.Month = strftime('%Y-%m', i.InvoiceDate)
LEFT JOIN (SELECT InvoiceId, SUM(RefundAmount) AS Refunded FROM Refund GROUP BY InvoiceId) r
       ON r.InvoiceId = i.InvoiceId
WHERE i.InvoiceStatus = 'settled'
  AND c.AccountType NOT IN ('internal', 'test')
  AND (s.AcquiredDate IS NULL OR i.InvoiceDate >= s.AcquiredDate)
GROUP BY 1, 2, 3, 4
"""


def rebuild(con: sqlite3.Connection) -> int:
    con.execute("DELETE FROM MonthlyRevenueRollup")
    con.execute(ROLLUP_SQL)
    con.commit()
    return con.execute("SELECT COUNT(*) FROM MonthlyRevenueRollup").fetchone()[0]


if __name__ == "__main__":
    with sqlite3.connect(DB) as con:
        print(f"MonthlyRevenueRollup rebuilt: {rebuild(con)} rows")
