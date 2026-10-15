"""Fetch job descriptions from public job board APIs."""

import html
import re

import requests

TIMEOUT = 30


def clean_html(text):
    """Turn HTML into plain text. Handles HTML that was escaped, like &lt;p&gt;."""
    text = html.unescape(text or "")       # &lt;p&gt; -> <p>
    text = re.sub(r"<[^>]+>", " ", text)   # remove tags
    text = html.unescape(text)             # &amp; -> &
    return re.sub(r"\s+", " ", text).strip()


def fetch_lever(company):
    """Return {job_id: description} for every open job at one Lever company."""
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
    res = requests.get(url, timeout=TIMEOUT)
    if res.status_code == 404:
        return {}
    res.raise_for_status()

    jobs = {}
    for job in res.json():
        parts = [job.get("descriptionPlain", "")]
        for section in job.get("lists", []):
            parts.append(section.get("text", ""))
            parts.append(clean_html(section.get("content", "")))
        jobs[job["id"]] = "\n".join(p for p in parts if p).strip()
    return jobs

def fetch_greenhouse(board):
    """Return {job_id: description} for every open job on one Greenhouse board."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
    res = requests.get(url, timeout=TIMEOUT)
    if res.status_code == 404:
        return {}
    res.raise_for_status()
    return {
        str(job["id"]): clean_html(job.get("content", ""))
        for job in res.json().get("jobs", [])
    }

def fetch_ashby(org):
    """Return {job_id: description} for every open job on one Ashby board."""
    url = f"https://api.ashbyhq.com/posting-api/job-board/{org}"
    res = requests.get(url, timeout=TIMEOUT)
    if res.status_code == 404:
        return {}
    res.raise_for_status()
    return {
        job["id"]: job.get("descriptionPlain") or clean_html(job.get("descriptionHtml", ""))
        for job in res.json().get("jobs", [])
    }

PATTERNS = [
    ("greenhouse", re.compile(r"greenhouse\.io/(?!embed)([^/?#]+)/jobs/(\d+)")),
    ("greenhouse", re.compile(r"greenhouse\.io/embed/job_app\?.*?for=([^&#]+).*?token=(\d+)")),
    ("lever",      re.compile(r"jobs\.lever\.co/([^/?#]+)/([0-9a-f-]{36})")),
    ("ashby",      re.compile(r"jobs\.ashbyhq\.com/([^/?#]+)/([0-9a-f-]{36})")),
]


def parse_board(url):
    """Return (board, company, job_id) for a supported URL, or None."""
    for board, pattern in PATTERNS:
        match = pattern.search(url or "")
        if match:
            return board, match.group(1), match.group(2)
    return None
    
if __name__ == "__main__":
    tests = [
        "https://job-boards.greenhouse.io/astranis/jobs/4652765007",
        "https://boards.greenhouse.io/embed/job_app?for=imc&token=7012345",
        "https://jobs.lever.co/hermeus/51378fa0-0327-45fd-9420-b6e7d8b56440/apply",
        "https://jobs.ashbyhq.com/bedrock-robotics/0f1e2d3c-4b5a-6978-8a9b-0c1d2e3f4a5b/application",
        "https://www.tesla.com/careers/search/job/12345",
    ]
    for url in tests:
        print(parse_board(url), "<-", url)