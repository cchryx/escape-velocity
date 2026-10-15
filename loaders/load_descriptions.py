"""Loader 2: save job descriptions from Greenhouse, Lever and Ashby.

Only looks at open postings with no description yet.
Fetches each company's board once and matches jobs by ID.
"""

import os
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

import psycopg
from dotenv import load_dotenv

from descriptions import fetch_ashby, fetch_greenhouse, fetch_lever, parse_board

FETCHERS = {"greenhouse": fetch_greenhouse, "lever": fetch_lever, "ashby": fetch_ashby}

TODO_SQL = """
select id, url from postings
where active
  and description is null
  and (description_checked_at is null or description_checked_at < now() - interval '7 days')
"""

SAVE_SQL = """
update postings
set description = %(description)s,
    description_source = %(source)s,
    description_checked_at = now()
where id = %(id)s
"""


def fetch_board(key):
    """Fetch one company's jobs. Returns (key, jobs). Errors give an empty dict."""
    board, company = key
    try:
        return key, FETCHERS[board](company)
    except Exception as err:  # one bad board should not stop the rest
        print(f"  skip {board}/{company}: {err}")
        return key, {}


def main():
    load_dotenv()
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        sys.exit("Set DATABASE_URL first (in .env or the environment).")

    with psycopg.connect(db_url) as conn, conn.cursor() as cur:
        cur.execute(TODO_SQL)
        todo = cur.fetchall()

        # Group postings by (board, company) so each board is fetched once.
        groups = defaultdict(list)
        for posting_id, url in todo:
            parsed = parse_board(url)
            if parsed:
                board, company, job_id = parsed
                groups[(board, company)].append((posting_id, job_id))
        print(f"{len(todo)} postings need a description. "
              f"{sum(len(v) for v in groups.values())} are on supported boards, "
              f"across {len(groups)} companies.")

        # Fetch 8 boards at a time.
        with ThreadPoolExecutor(max_workers=8) as pool:
            boards = dict(pool.map(fetch_board, groups))

        rows = []
        found = 0
        for key, postings in groups.items():
            jobs = boards.get(key, {})
            for posting_id, job_id in postings:
                text = jobs.get(job_id)
                if text:
                    found += 1
                rows.append({"id": posting_id, "description": text or None,
                             "source": key[0] if text else None})
        cur.executemany(SAVE_SQL, rows)

    print(f"Saved {found} descriptions. {len(rows) - found} not found (job closed or hidden).")


if __name__ == "__main__":
    main()