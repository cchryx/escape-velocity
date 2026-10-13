"""Loader 1: pull Summer 2027 internships from the SimplifyJobs list into Supabase.

- Keeps listings that are visible and include the "Summer 2027" term.
- Inserts new postings and updates changed ones by id.
- Marks postings as closed (active = false) when they are closed or gone from the list.
- Never touches description, skills or embedding. Later loaders fill those.

Run:  python loaders/load_postings.py
Needs DATABASE_URL in the environment or in a .env file at the repo root.
"""

import os
import sys
from datetime import datetime, timezone

import psycopg
import requests
from dotenv import load_dotenv

LISTINGS_URL = (
    "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/"
    "dev/.github/scripts/listings.json"
)
TERM = "Summer 2027"

UPSERT_SQL = """
insert into postings (id, company, title, url, locations, terms, category, active, date_posted, updated_at)
values (%(id)s, %(company)s, %(title)s, %(url)s, %(locations)s, %(terms)s, %(category)s, %(active)s, %(date_posted)s, now())
on conflict (id) do update set
  company     = excluded.company,
  title       = excluded.title,
  url         = excluded.url,
  locations   = excluded.locations,
  terms       = excluded.terms,
  category    = excluded.category,
  active      = excluded.active,
  date_posted = excluded.date_posted,
  updated_at  = now()
where (postings.company, postings.title, postings.url, postings.locations,
       postings.terms, postings.category, postings.active, postings.date_posted)
   is distinct from
      (excluded.company, excluded.title, excluded.url, excluded.locations,
       excluded.terms, excluded.category, excluded.active, excluded.date_posted)
"""


def fetch_listings():
    res = requests.get(LISTINGS_URL, timeout=60)
    res.raise_for_status()
    return res.json()


def to_row(item):
    posted = item.get("date_posted")
    return {
        "id": str(item["id"]),
        "company": (item.get("company_name") or "").strip(),
        "title": (item.get("title") or "").strip(),
        "url": item.get("url") or "",
        "locations": item.get("locations") or [],
        "terms": item.get("terms") or [],
        "category": item.get("category"),
        "active": bool(item.get("active")),
        "date_posted": datetime.fromtimestamp(posted, tz=timezone.utc) if posted else None,
    }


def keep(item):
    return (
        item.get("is_visible", True)
        and TERM in (item.get("terms") or [])
        and item.get("id")
        and item.get("company_name")
        and item.get("title")
        and item.get("url")
    )


def main():
    load_dotenv()
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        sys.exit("Set DATABASE_URL first (in .env or the environment).")

    items = fetch_listings()
    rows = [to_row(x) for x in items if keep(x)]
    open_ids = [r["id"] for r in rows if r["active"]]
    print(f"Fetched {len(items)} listings. Kept {len(rows)} for {TERM}, {len(open_ids)} open.")

    with psycopg.connect(db_url) as conn, conn.cursor() as cur:
        cur.execute("select id from postings")
        before = {r[0] for r in cur.fetchall()}

        # One batched round trip instead of one per row.
        cur.executemany(UPSERT_SQL, rows)
        added = sum(1 for r in rows if r["id"] not in before)
        updated = cur.rowcount - added

        # Postings that were open before but are no longer open in the list.
        cur.execute(
            "update postings set active = false, updated_at = now() "
            "where active and not (id = any(%s))",
            (open_ids,),
        )
        closed = cur.rowcount

        cur.execute("select count(*) from postings where active")
        open_total = cur.fetchone()[0]

    print(f"Added {added}, updated {updated}, closed {closed}. Open postings now: {open_total}.")


if __name__ == "__main__":
    main()
