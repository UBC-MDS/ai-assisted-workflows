"""Build evals/benchmark.yaml — question / gold-SQL pairs, verified by execution.

LAYER 0 ONLY.

Every pair is executed against data/askdb.sqlite before it is written; a pair whose gold
SQL errors or returns nothing is a build failure. Questions say exactly what to return, so
grading compares answers, not column choices.

Categories:
  revenue    -- finance revenue over windows from one month to a year
  fiscal     -- fiscal calendar and invoice-status questions
  catalog    -- units sold, catalogue facts
  customer   -- customer counts and lists
  reference  -- stores, plans, rates, staff
"""

import sqlite3
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "askdb.sqlite"
OUT = ROOT / "evals" / "benchmark.yaml"

REV = "(i.Subtotal - COALESCE(rf.Refunded, 0)) * x.RateToUSD"
FROM_REV = """FROM Invoice i
JOIN Customer c ON c.CustomerId = i.CustomerId
JOIN Store s ON s.StoreId = i.StoreId
JOIN ExchangeRate x ON x.CurrencyCode = i.CurrencyCode AND x.Month = strftime('%Y-%m', i.InvoiceDate)
LEFT JOIN (SELECT InvoiceId, SUM(RefundAmount) AS Refunded FROM Refund GROUP BY InvoiceId) rf
       ON rf.InvoiceId = i.InvoiceId
WHERE i.InvoiceStatus = 'settled'
  AND c.AccountType NOT IN ('internal', 'test')
  AND (s.AcquiredDate IS NULL OR i.InvoiceDate >= s.AcquiredDate)"""
POP = """FROM Customer c
JOIN Store s ON s.StoreId = c.HomeStoreId
WHERE c.AccountType IN ('retail', 'reseller')
  AND (s.AcquiredDate IS NULL OR c.FirstPurchaseDate >= s.AcquiredDate)"""
UNITS = """FROM InvoiceLine il
JOIN Invoice i ON i.InvoiceId = il.InvoiceId
JOIN Track t ON t.TrackId = il.TrackId
WHERE i.InvoiceStatus = 'settled'"""

PAIRS = [
    # ---- revenue -------------------------------------------------------------------
    ("revenue", "What was our revenue in calendar 2024? Return a single number.",
     f"SELECT ROUND(SUM({REV}), 2) {FROM_REV} AND i.InvoiceDate BETWEEN '2024-01-01' AND '2024-12-31'"),
    ("revenue", "What was revenue for July, August and September 2024 combined? Return a single number.",
     f"SELECT ROUND(SUM({REV}), 2) {FROM_REV} AND i.InvoiceDate BETWEEN '2024-07-01' AND '2024-09-30'"),
    ("revenue", "Show revenue by region for October to December 2024. Return the region and the revenue.",
     f"SELECT s.Region, ROUND(SUM({REV}), 2) {FROM_REV} AND i.InvoiceDate BETWEEN '2024-10-01' AND '2024-12-31' GROUP BY 1"),
    ("revenue", "Show revenue by channel for November 2025. Return the channel and the revenue.",
     f"SELECT i.Channel, ROUND(SUM({REV}), 2) {FROM_REV} AND i.InvoiceDate BETWEEN '2025-11-01' AND '2025-11-30' GROUP BY 1"),
    ("revenue", "Show revenue by store for calendar 2025. Return the store name and the revenue.",
     f"SELECT s.Name, ROUND(SUM({REV}), 2) {FROM_REV} AND i.InvoiceDate BETWEEN '2025-01-01' AND '2025-12-31' GROUP BY 1"),
    ("revenue", "What was revenue in December 2025? Return a single number.",
     f"SELECT ROUND(SUM({REV}), 2) {FROM_REV} AND i.InvoiceDate BETWEEN '2025-12-01' AND '2025-12-31'"),
    ("revenue", "Which calendar month of 2024 had the highest revenue? Return the month as YYYY-MM and its revenue.",
     f"SELECT strftime('%Y-%m', i.InvoiceDate), ROUND(SUM({REV}), 2) {FROM_REV} AND i.InvoiceDate BETWEEN '2024-01-01' AND '2024-12-31' GROUP BY 1 ORDER BY 2 DESC LIMIT 1"),
    ("revenue", "What was revenue from reseller accounts in calendar 2025? Return a single number.",
     f"SELECT ROUND(SUM({REV}), 2) {FROM_REV} AND c.AccountType = 'reseller' AND i.InvoiceDate BETWEEN '2025-01-01' AND '2025-12-31'"),
    ("revenue", "What was app-channel revenue at the London store from April to June 2025? Return a single number.",
     f"SELECT ROUND(SUM({REV}), 2) {FROM_REV} AND s.Name = 'London' AND i.Channel = 'app' AND i.InvoiceDate BETWEEN '2025-04-01' AND '2025-06-30'"),
    ("revenue", "Show monthly revenue for calendar 2025. Return the month as YYYY-MM and the revenue.",
     f"SELECT strftime('%Y-%m', i.InvoiceDate), ROUND(SUM({REV}), 2) {FROM_REV} AND i.InvoiceDate BETWEEN '2025-01-01' AND '2025-12-31' GROUP BY 1"),

    # ---- fiscal / invoice status -------------------------------------------------------
    ("fiscal", "Which fiscal year and fiscal quarter does March 2025 fall in? Return the fiscal year and the quarter.",
     "SELECT FiscalYear, FiscalQuarter FROM FiscalMonth WHERE Month = '2025-03'"),
    ("fiscal", "What was revenue in fiscal Q1 of FY2026? Return a single number.",
     f"SELECT ROUND(SUM({REV}), 2) {FROM_REV} AND i.InvoiceDate BETWEEN '2025-02-01' AND '2025-04-30'"),
    ("fiscal", "What was revenue in fiscal year 2025? Return a single number.",
     f"SELECT ROUND(SUM({REV}), 2) {FROM_REV} AND i.InvoiceDate BETWEEN '2024-02-01' AND '2025-01-31'"),
    ("fiscal", "How many settled invoices were there in December 2025? Return a single number.",
     "SELECT COUNT(*) FROM Invoice WHERE InvoiceStatus = 'settled' AND InvoiceDate BETWEEN '2025-12-01' AND '2025-12-31'"),
    ("fiscal", "How many invoices were voided in calendar 2024? Return a single number.",
     "SELECT COUNT(*) FROM Invoice WHERE InvoiceStatus = 'void' AND InvoiceDate BETWEEN '2024-01-01' AND '2024-12-31'"),
    ("fiscal", "How many invoices are still pending? Return a single number.",
     "SELECT COUNT(*) FROM Invoice WHERE InvoiceStatus = 'pending'"),

    # ---- catalog -----------------------------------------------------------------------
    ("catalog", "How many tracks are in the catalogue? Return a single number.",
     "SELECT COUNT(*) FROM Track"),
    ("catalog", "Which genre sold the most units in calendar 2025? Return just the genre name.",
     f"SELECT g.Name {UNITS.replace('WHERE', 'JOIN Genre g ON g.GenreId = t.GenreId WHERE')} AND i.InvoiceDate BETWEEN '2025-01-01' AND '2025-12-31' GROUP BY g.Name ORDER BY SUM(il.Quantity) DESC LIMIT 1"),
    ("catalog", "Which 5 artists sold the most units in calendar 2024? Return the artist name and the units.",
     f"SELECT ar.Name, SUM(il.Quantity) {UNITS.replace('WHERE', 'JOIN Album al ON al.AlbumId = t.AlbumId JOIN Artist ar ON ar.ArtistId = al.ArtistId WHERE')} AND i.InvoiceDate BETWEEN '2024-01-01' AND '2024-12-31' GROUP BY ar.Name ORDER BY 2 DESC LIMIT 5"),
    ("catalog", "How many units did we sell per media type in calendar 2025? Return the media type name and the units.",
     f"SELECT mt.Name, SUM(il.Quantity) {UNITS.replace('WHERE', 'JOIN MediaType mt ON mt.MediaTypeId = t.MediaTypeId WHERE')} AND i.InvoiceDate BETWEEN '2025-01-01' AND '2025-12-31' GROUP BY mt.Name"),
    ("catalog", "What is the average track length in minutes, to one decimal place? Return a single number.",
     "SELECT ROUND(AVG(Milliseconds) / 60000.0, 1) FROM Track"),
    ("catalog", "How many albums are in the catalogue? Return a single number.",
     "SELECT COUNT(*) FROM Album"),
    ("catalog", "Which artist sold the most units in calendar 2025? Return the artist name and the units.",
     f"SELECT ar.Name, SUM(il.Quantity) {UNITS.replace('WHERE', 'JOIN Album al ON al.AlbumId = t.AlbumId JOIN Artist ar ON ar.ArtistId = al.ArtistId WHERE')} AND i.InvoiceDate BETWEEN '2025-01-01' AND '2025-12-31' GROUP BY ar.ArtistId ORDER BY 2 DESC LIMIT 1"),
    ("catalog", "How many genres are there? Return a single number.",
     "SELECT COUNT(*) FROM Genre"),

    # ---- customer ------------------------------------------------------------------------
    ("customer", "How many customers do we have? Return a single number.",
     f"SELECT COUNT(*) {POP}"),
    ("customer", "How many customers do we have in each region? Return the region and the count.",
     f"SELECT s.Region, COUNT(*) {POP} GROUP BY s.Region"),
    ("customer", "Who were our top 10 customers by revenue in calendar 2025? Return the customer ID and the revenue.",
     f"""SELECT i.CustomerId, ROUND(SUM({REV}), 2) {FROM_REV}
  AND i.InvoiceDate BETWEEN '2025-01-01' AND '2025-12-31'
  AND i.CustomerId IN (SELECT c.CustomerId {POP})
GROUP BY i.CustomerId ORDER BY 2 DESC LIMIT 10"""),
    ("customer", "How many reseller accounts do we have? Return a single number.",
     f"SELECT COUNT(*) {POP} AND c.AccountType = 'reseller'"),
    ("customer", "How many customers does the London store have? Return a single number.",
     f"SELECT COUNT(*) {POP} AND s.Name = 'London'"),
    ("customer", "How many customers made their first purchase in calendar 2025? Return a single number.",
     f"SELECT COUNT(*) {POP} AND c.FirstPurchaseDate BETWEEN '2025-01-01' AND '2025-12-31'"),
    ("customer", "How many retail customers do we have in the NA region? Return a single number.",
     f"SELECT COUNT(*) {POP} AND c.AccountType = 'retail' AND s.Region = 'NA'"),
    ("customer", "How many customers have an active subscription? Return a single number.",
     f"SELECT COUNT(DISTINCT c.CustomerId) {POP} AND c.CustomerId IN (SELECT CustomerId FROM Subscription WHERE EndDate IS NULL)"),

    # ---- reference -------------------------------------------------------------------------
    ("reference", "How many stores do we have? Return a single number.",
     "SELECT COUNT(*) FROM Store"),
    ("reference", "What currency does the London store use? Return the currency code.",
     "SELECT CurrencyCode FROM Store WHERE Name = 'London'"),
    ("reference", "List our subscription plans and their monthly price. Return the plan name and the price.",
     "SELECT Name, MonthlyPriceUSD FROM Plan"),
    ("reference", "What was the EUR to USD exchange rate in November 2025? Return a single number.",
     "SELECT RateToUSD FROM ExchangeRate WHERE CurrencyCode = 'EUR' AND Month = '2025-11'"),
    ("reference", "Which store did we acquire, and when? Return the store name and the acquisition date.",
     "SELECT Name, AcquiredDate FROM Store WHERE AcquiredDate IS NOT NULL"),
    ("reference", "List our support reps. Return their first and last names.",
     "SELECT FirstName, LastName FROM Employee WHERE Title = 'Sales Support Agent'"),
    ("reference", "What is the tax rate at the Berlin store? Return a single number.",
     "SELECT TaxRate FROM Store WHERE Name = 'Berlin'"),
    ("reference", "How many employees do we have? Return a single number.",
     "SELECT COUNT(*) FROM Employee"),
]


def main():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    out = []
    for i, (cat, q, sql) in enumerate(PAIRS, 1):
        sql = " ".join(sql.split())
        rows = con.execute(sql).fetchall()
        if not rows or rows == [(None,)]:
            raise SystemExit(f"pair {i} returned nothing: {q}")
        out.append({"id": f"{cat[:3]}-{i:02d}", "category": cat, "question": q, "gold_sql": sql})
    header = (
        "# askdb evaluation benchmark — generated by scripts/build_benchmark.py\n"
        "#\n"
        "# Every gold_sql has been executed against data/askdb.sqlite. Grading runs the\n"
        "# question through askdb and compares result sets with the gold result.\n"
        "#\n"
        "# Pair types:\n"
        "#   (default)                 compare rows with the gold SQL's rows\n"
        "#   expect: refusal           askdb must refuse the question\n"
        "#   expect: no_erased_pii     askdb's answer must contain no personal data of a\n"
        "#                             customer who requested erasure\n\n"
    )
    OUT.write_text(header + yaml.safe_dump({"pairs": out}, sort_keys=False, width=1000, allow_unicode=True))
    from collections import Counter
    print(f"wrote {OUT.relative_to(ROOT)}: {len(out)} verified pairs")
    for c, n in sorted(Counter(p["category"] for p in out).items()):
        print(f"  {c:10s} {n}")


if __name__ == "__main__":
    main()
