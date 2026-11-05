"""Build data/askdb.sqlite — the analytics warehouse askdb answers questions from.

LAYER 0 ONLY. Deterministic (seeded). Never run during the workshop.

The music catalogue (artists, albums, tracks, genres) comes from the public Chinook
sample database. Everything about customers and money is synthetic, generated here:
six stores in five currencies, ~6,000 customers, ~50k invoices, refunds, subscriptions,
monthly exchange rates, a fiscal calendar and a pre-aggregated revenue rollup.

The property the workshop depends on is built in deliberately: customers who exercise
their GDPR right to erasure are overwhelmingly customers who had already stopped buying.
"""

import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from rebuild_rollup import rebuild as rebuild_rollup

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "chinook_source.sqlite"
OUT = ROOT / "data" / "askdb.sqlite"

SEED = 20261017
START = date(2022, 1, 1)
SNAPSHOT = date(2025, 12, 31)          # "data as of"
LAST_FIRST_PURCHASE = date(2025, 6, 30)
N_CUSTOMERS = 6000

ERASURE_RATE = 0.14                    # share of retail/reseller customers who request erasure
CHURN_IF_ERASED = 0.90                 # P(not retained at 12 months | erased)
CHURN_IF_NOT_ERASED = 0.38             # P(not retained at 12 months | not erased)

STORES = [
    # id, name, region, country, currency, tax rate, opened, acquired, weight
    (1, "Toronto",   "NA",    "Canada",         "CAD", 0.13, "2015-03-01", None,         0.15),
    (2, "New York",  "NA",    "United States",  "USD", 0.08, "2014-06-01", None,         0.25),
    (3, "London",    "EU",    "United Kingdom", "GBP", 0.20, "2016-09-01", None,         0.20),
    (4, "Berlin",    "EU",    "Germany",        "EUR", 0.19, "2018-02-01", None,         0.15),
    (5, "São Paulo", "LATAM", "Brazil",         "BRL", 0.17, "2012-01-01", "2023-07-01", 0.12),
    (6, "Sydney",    "APAC",  "Australia",      "AUD", 0.10, "2019-11-01", None,         0.13),
]
BASE_RATE = {"CAD": 0.74, "USD": 1.0, "GBP": 1.27, "EUR": 1.09, "BRL": 0.20, "AUD": 0.66}
PLANS = [(1, "Basic", 9.99), (2, "Premium", 14.99), (3, "Family", 19.99)]

FIRST = ["Jane", "Omar", "Priya", "Lucas", "Mei", "Tomás", "Aisha", "Ben", "Sofia", "Kenji",
         "Chloe", "Rahul", "Ana", "Felix", "Zoe", "Mateo", "Lena", "Arjun", "Hana", "Leo",
         "Nadia", "Sam", "Ines", "Ravi", "Emma", "Diego", "Yuki", "Noah", "Amara", "Jonas"]
LAST = ["Doe", "Silva", "Sharma", "Martin", "Chen", "Costa", "Khan", "Taylor", "Rossi", "Sato",
        "Dubois", "Patel", "Santos", "Weber", "Brown", "Lopez", "Schmidt", "Iyer", "Kim", "Moreau",
        "Haddad", "Wilson", "Ferreira", "Nair", "Clarke", "Garcia", "Tanaka", "Murphy", "Okafor", "Novak"]
DOMAINS = ["gmail.com", "outlook.com", "yahoo.com", "proton.me", "icloud.com", "hey.com"]

SCHEMA = """
CREATE TABLE Store (
    StoreId INTEGER PRIMARY KEY, Name TEXT NOT NULL, Region TEXT NOT NULL,
    Country TEXT NOT NULL, CurrencyCode TEXT NOT NULL, TaxRate NUMERIC NOT NULL,
    OpenedDate DATE NOT NULL, AcquiredDate DATE
);
CREATE TABLE Employee (
    EmployeeId INTEGER PRIMARY KEY, FirstName TEXT NOT NULL, LastName TEXT NOT NULL,
    Title TEXT, ReportsTo INTEGER REFERENCES Employee(EmployeeId), Email TEXT
);
CREATE TABLE Customer (
    CustomerId INTEGER PRIMARY KEY,
    FirstName TEXT, LastName TEXT, Email TEXT, Phone TEXT, Address TEXT, City TEXT,
    Country TEXT NOT NULL,
    AccountType TEXT NOT NULL CHECK (AccountType IN ('retail','reseller','internal','test')),
    HomeStoreId INTEGER NOT NULL REFERENCES Store(StoreId),
    SupportRepId INTEGER REFERENCES Employee(EmployeeId),
    FirstPurchaseDate DATE NOT NULL,
    LastActiveDate DATE NOT NULL
);
CREATE TABLE ErasureRequest (
    RequestId INTEGER PRIMARY KEY,
    CustomerId INTEGER NOT NULL REFERENCES Customer(CustomerId),
    ReceivedDate DATE NOT NULL,
    Status TEXT NOT NULL CHECK (Status IN ('received','verified','completed','rejected','withdrawn','on_hold')),
    StatusDate DATE NOT NULL,
    Note TEXT
);
CREATE TABLE Artist (ArtistId INTEGER PRIMARY KEY, Name TEXT);
CREATE TABLE Album (AlbumId INTEGER PRIMARY KEY, Title TEXT NOT NULL,
                    ArtistId INTEGER NOT NULL REFERENCES Artist(ArtistId));
CREATE TABLE Genre (GenreId INTEGER PRIMARY KEY, Name TEXT);
CREATE TABLE MediaType (MediaTypeId INTEGER PRIMARY KEY, Name TEXT);
CREATE TABLE Track (
    TrackId INTEGER PRIMARY KEY, Name TEXT NOT NULL,
    AlbumId INTEGER REFERENCES Album(AlbumId), MediaTypeId INTEGER NOT NULL REFERENCES MediaType(MediaTypeId),
    GenreId INTEGER REFERENCES Genre(GenreId), Composer TEXT, Milliseconds INTEGER NOT NULL,
    UnitPriceUSD NUMERIC NOT NULL
);
CREATE TABLE Invoice (
    InvoiceId INTEGER PRIMARY KEY,
    CustomerId INTEGER NOT NULL REFERENCES Customer(CustomerId),
    StoreId INTEGER NOT NULL REFERENCES Store(StoreId),
    InvoiceDate DATE NOT NULL,
    Channel TEXT NOT NULL CHECK (Channel IN ('web','app','store','reseller')),
    CurrencyCode TEXT NOT NULL,
    Subtotal NUMERIC NOT NULL, TaxAmount NUMERIC NOT NULL, Total NUMERIC NOT NULL,
    InvoiceStatus TEXT NOT NULL CHECK (InvoiceStatus IN ('settled','pending','void','comped'))
);
CREATE TABLE InvoiceLine (
    InvoiceLineId INTEGER PRIMARY KEY,
    InvoiceId INTEGER NOT NULL REFERENCES Invoice(InvoiceId),
    TrackId INTEGER NOT NULL REFERENCES Track(TrackId),
    UnitPrice NUMERIC NOT NULL, Quantity INTEGER NOT NULL, DiscountAmount NUMERIC NOT NULL
);
CREATE TABLE Refund (
    RefundId INTEGER PRIMARY KEY,
    InvoiceId INTEGER NOT NULL REFERENCES Invoice(InvoiceId),
    RefundDate DATE NOT NULL, RefundAmount NUMERIC NOT NULL, Reason TEXT NOT NULL
);
CREATE TABLE ExchangeRate (
    CurrencyCode TEXT NOT NULL, Month TEXT NOT NULL, RateToUSD NUMERIC NOT NULL,
    PRIMARY KEY (CurrencyCode, Month)
);
CREATE TABLE FiscalMonth (
    Month TEXT PRIMARY KEY, FiscalYear INTEGER NOT NULL, FiscalQuarter INTEGER NOT NULL
);
CREATE TABLE Plan (PlanId INTEGER PRIMARY KEY, Name TEXT NOT NULL, MonthlyPriceUSD NUMERIC NOT NULL);
CREATE TABLE Subscription (
    SubscriptionId INTEGER PRIMARY KEY,
    CustomerId INTEGER NOT NULL REFERENCES Customer(CustomerId),
    PlanId INTEGER NOT NULL REFERENCES Plan(PlanId),
    StartDate DATE NOT NULL, EndDate DATE
);
CREATE TABLE MonthlyRevenueRollup (
    Month TEXT NOT NULL, StoreId INTEGER NOT NULL, Channel TEXT NOT NULL,
    AccountType TEXT NOT NULL, NetRevenueUSD NUMERIC NOT NULL, InvoiceCount INTEGER NOT NULL,
    PRIMARY KEY (Month, StoreId, Channel, AccountType)
);
CREATE INDEX ix_invoice_customer ON Invoice(CustomerId);
CREATE INDEX ix_invoice_date ON Invoice(InvoiceDate);
CREATE INDEX ix_line_invoice ON InvoiceLine(InvoiceId);
CREATE INDEX ix_line_track ON InvoiceLine(TrackId);
CREATE INDEX ix_refund_invoice ON Refund(InvoiceId);
CREATE INDEX ix_customer_store ON Customer(HomeStoreId);
"""


def months(start, end):
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield f"{y:04d}-{m:02d}"
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def add_months(d, n):
    y, m = divmod(d.month - 1 + n, 12)
    y, m = d.year + y, m + 1
    last = [31, 29 if y % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
    return date(y, m, min(d.day, last))


def rand_date(rng, lo, hi):
    return lo + timedelta(days=rng.randint(0, max(0, (hi - lo).days)))


def make_email(rng, first, last, n):
    local = f"{first}.{last}".lower()
    r = rng.random()
    if r < 0.08:
        local = f"{first.lower()}+music"          # plus-addressed
    elif r < 0.23:
        local = f"{first}.{last}"                 # mixed case
    if n % 7 == 0:
        local += str(n % 97)
    dom = rng.choice(DOMAINS)
    if r >= 0.08 and r < 0.23 and rng.random() < 0.5:
        dom = dom.capitalize()
    return f"{local}@{dom}".replace("á", "a").replace("ã", "a").replace("é", "e")


def erasure_requests(customers, erasures):
    """GDPR erasure requests as the privacy team's case system records them — messy on purpose.

    Uses its own random stream, so adding or changing it never moves any other data.
    - Customers who asked to be erased (the `erasures` list) mostly stopped buying first.
      Their latest request is completed, verified, received, rejected (identity not
      confirmed) or on hold (records under a tax audit cannot be purged yet).
    - Some of them withdrew an earlier request before making the final one.
    - A smaller group of active customers sent a request and then withdrew it, or had it
      rejected, and carried on buying.
    """
    rq = random.Random(SEED + 101)
    rows = []

    def add(cid, received, status, note=None):
        received = min(received, SNAPSHOT - timedelta(days=1))
        if status == "received":
            status_date = received
        else:
            status_date = min(received + timedelta(days=rq.randint(3, 60)), SNAPSHOT)
        rows.append((len(rows) + 1, cid, received.isoformat(), status, status_date.isoformat(), note))

    for cid, acct, first, last_active, erased_at in erasures:
        note = "request from the account's named contact" if acct == "reseller" else None
        if rq.random() < 0.10 and (erased_at - first).days > 120:
            add(cid, rand_date(rq, first, erased_at - timedelta(days=90)), "withdrawn", note)
        status = rq.choices(["completed", "verified", "received", "on_hold", "rejected"],
                            [0.60, 0.15, 0.10, 0.07, 0.08])[0]
        add(cid, erased_at, status,
            "tax audit: records under legal hold" if status == "on_hold" else
            "identity could not be verified" if status == "rejected" else note)

    erased_ids = {e[0] for e in erasures}
    for c in customers:
        cid, acct, first = c[0], c[8], date.fromisoformat(c[11])
        if acct in ("retail", "reseller") and cid not in erased_ids and rq.random() < 0.04:
            add(cid, rand_date(rq, first, SNAPSHOT - timedelta(days=30)),
                rq.choices(["withdrawn", "rejected"], [0.6, 0.4])[0])
    rows.sort(key=lambda r: (r[2], r[1]))
    return [(i + 1, *r[1:]) for i, r in enumerate(rows)]


def main():
    rng = random.Random(SEED)
    if OUT.exists():
        OUT.unlink()
    src = sqlite3.connect(SOURCE)
    con = sqlite3.connect(OUT)
    con.executescript(SCHEMA)

    # --- reference data -------------------------------------------------------------
    con.executemany("INSERT INTO Store VALUES (?,?,?,?,?,?,?,?)", [s[:8] for s in STORES])
    con.executemany("INSERT INTO Employee VALUES (?,?,?,?,?,?)", src.execute(
        "SELECT EmployeeId, FirstName, LastName, Title, ReportsTo, Email FROM Employee").fetchall())
    for t, cols in [("Artist", "ArtistId, Name"), ("Album", "AlbumId, Title, ArtistId"),
                    ("Genre", "GenreId, Name"), ("MediaType", "MediaTypeId, Name")]:
        rows = src.execute(f"SELECT {cols} FROM {t}").fetchall()
        con.executemany(f"INSERT INTO {t} VALUES ({','.join('?' * len(rows[0]))})", rows)
    tracks = src.execute("SELECT TrackId, Name, AlbumId, MediaTypeId, GenreId, Composer, "
                         "Milliseconds, UnitPrice FROM Track").fetchall()
    con.executemany("INSERT INTO Track VALUES (?,?,?,?,?,?,?,?)", tracks)
    track_price = {t[0]: t[7] for t in tracks}
    track_ids = list(track_price)

    rate = {}
    for cur, base in BASE_RATE.items():
        drift = 1.0
        for mo in months(START, SNAPSHOT):
            if cur != "USD":
                drift *= 1 + rng.uniform(-0.02, 0.02)
            rate[(cur, mo)] = round(base * drift, 4) if cur != "USD" else 1.0
    con.executemany("INSERT INTO ExchangeRate VALUES (?,?,?)",
                    [(c, m, r) for (c, m), r in sorted(rate.items())])

    fiscal = []
    for mo in months(START, date(2026, 12, 31)):
        y, m = int(mo[:4]), int(mo[5:])
        fy = y + 1 if m >= 2 else y          # FY named for the calendar year it ends in
        fq = ((m - 2) % 12) // 3 + 1
        fiscal.append((mo, fy, fq))
    con.executemany("INSERT INTO FiscalMonth VALUES (?,?,?)", fiscal)
    con.executemany("INSERT INTO Plan VALUES (?,?,?)", PLANS)

    # --- customers --------------------------------------------------------------------
    store_ids = [s[0] for s in STORES]
    store_w = [s[8] for s in STORES]
    store = {s[0]: s for s in STORES}
    customers, subs, erasures = [], [], []
    for cid in range(1, N_CUSTOMERS + 1):
        sid = rng.choices(store_ids, store_w)[0]
        r = rng.random()
        acct = "retail" if r < 0.85 else "reseller" if r < 0.94 else "internal" if r < 0.97 else "test"
        first_name, last_name = rng.choice(FIRST), rng.choice(LAST)
        first = rand_date(rng, START, LAST_FIRST_PURCHASE)

        real = acct in ("retail", "reseller")
        erased = real and rng.random() < ERASURE_RATE
        churned = rng.random() < (CHURN_IF_ERASED if erased else CHURN_IF_NOT_ERASED)
        twelve = add_months(first, 12)
        if churned:
            last_active = first + timedelta(days=rng.randint(0, 330))
        elif erased:
            # retained past 12 months, then left and asked to be erased
            hi = SNAPSHOT - timedelta(days=60)
            last_active = rand_date(rng, twelve, hi) if twelve <= hi else first + timedelta(days=rng.randint(0, 330))
        else:
            last_active = SNAPSHOT if rng.random() < 0.6 else rand_date(rng, twelve, SNAPSHOT)
        # an erased customer stopped buying before they asked to be erased
        last_active = min(last_active, SNAPSHOT - timedelta(days=30) if erased else SNAPSHOT)

        erased_at = None
        if erased:
            lo = last_active + timedelta(days=1)
            erased_at = rand_date(rng, lo, lo + timedelta(days=330))
            if erased_at >= SNAPSHOT:   # wrap rather than clip, so requests don't pile up on the last day
                erased_at = lo + timedelta(days=(erased_at - lo).days % max(1, (SNAPSHOT - lo).days))

        if acct == "test":
            email = f"qa{cid}@askdb-test.example"
        elif acct == "internal":
            email = f"{first_name.lower()}.{last_name.lower()}{cid}@chinook-music.com"
        else:
            email = make_email(rng, first_name, last_name, cid)
        customers.append((
            cid, first_name, last_name, email,
            f"+{rng.randint(1, 99)} {rng.randint(100, 999)} {rng.randint(1000, 9999)}",
            f"{rng.randint(1, 999)} {rng.choice(['High', 'Main', 'King', 'Park', 'Mill'])} St",
            store[sid][1], store[sid][3], acct, sid, rng.choice([3, 4, 5]),
            first.isoformat(), last_active.isoformat(),
        ))
        if erased:
            erasures.append((cid, acct, first, last_active, erased_at))
        if real and rng.random() < 0.30:
            start = first + timedelta(days=rng.randint(0, 90))
            if start <= last_active:
                end = None if last_active >= SNAPSHOT else last_active
                subs.append((len(subs) + 1, cid, rng.choice([1, 1, 2, 2, 3]), start.isoformat(),
                             end.isoformat() if end else None))
    con.executemany("INSERT INTO Customer VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", customers)
    con.executemany("INSERT INTO ErasureRequest VALUES (?,?,?,?,?,?)", erasure_requests(customers, erasures))
    con.executemany("INSERT INTO Subscription VALUES (?,?,?,?,?)", subs)

    # --- invoices -----------------------------------------------------------------------
    invoices, lines, refunds = [], [], []
    for c in customers:
        cid, acct, sid = c[0], c[8], c[9]
        first, last_active = date.fromisoformat(c[11]), date.fromisoformat(c[12])
        cur, tax = store[sid][4], store[sid][5]
        gap = 18 if acct == "reseller" else 45
        d = first
        while d <= last_active:
            channel = "reseller" if acct == "reseller" else rng.choices(
                ["web", "app", "store"], [0.45, 0.35, 0.20])[0]
            n_lines = rng.randint(5, 25) if acct == "reseller" else rng.randint(1, 8)
            iid = len(invoices) + 1
            subtotal = 0.0
            fx = rate[(cur, d.strftime("%Y-%m"))]
            for _ in range(n_lines):
                tid = rng.choice(track_ids)
                price = round(track_price[tid] / fx, 2)
                qty = 1
                disc = round(price * 0.20, 2) if acct == "reseller" else (
                    round(price * rng.choice([0.1, 0.2, 0.3]), 2) if rng.random() < 0.10 else 0.0)
                lines.append((len(lines) + 1, iid, tid, price, qty, disc))
                subtotal += price * qty - disc
            subtotal = round(subtotal, 2)
            tax_amt = round(subtotal * tax, 2)
            if (SNAPSHOT - d).days < 7 and rng.random() < 0.5:
                status = "pending"
            else:
                r = rng.random()
                status = "settled" if r < 0.955 else "void" if r < 0.975 else "comped"
            invoices.append((iid, cid, sid, d.isoformat(), channel, cur,
                             subtotal, tax_amt, round(subtotal + tax_amt, 2), status))
            if status == "settled" and rng.random() < 0.05:
                amt = round(subtotal * rng.choice([0.3, 0.5, 1.0, 1.0]), 2)
                refunds.append((len(refunds) + 1, iid, (d + timedelta(days=rng.randint(3, 30))).isoformat(),
                                amt, rng.choice(["damaged file", "duplicate purchase", "not as described",
                                                 "accidental purchase"])))
            d += timedelta(days=max(1, int(rng.expovariate(1 / gap))))
    con.executemany("INSERT INTO Invoice VALUES (?,?,?,?,?,?,?,?,?,?)", invoices)
    con.executemany("INSERT INTO InvoiceLine VALUES (?,?,?,?,?,?)", lines)
    con.executemany("INSERT INTO Refund VALUES (?,?,?,?,?)", refunds)

    # --- the rollup: the data-platform ETL, as run nightly in production -------------
    rebuild_rollup(con)
    con.commit()
    con.execute("VACUUM")
    con.close()

    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  customers     {len(customers):>7,}")
    print(f"  invoices      {len(invoices):>7,}")
    print(f"  invoice lines {len(lines):>7,}")
    print(f"  refunds       {len(refunds):>7,}")
    print(f"  subscriptions {len(subs):>7,}")
    print(f"  size          {OUT.stat().st_size / 1e6:>7.1f} MB")


if __name__ == "__main__":
    main()
