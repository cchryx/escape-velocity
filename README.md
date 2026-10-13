# Escape Velocity

Find the internships that fit you. Get the courses that launch you there.

Upload your resume. Escape Velocity ranks open Summer 2027 internships by fit and lists the skills you are missing for each one. Then it suggests courses that teach those skills.

## Status

| Part | What | Status |
|---|---|---|
| 1 | Job finder | Building |
| 2 | Course finder | Planned |

## How it works

1. A daily job pulls Summer 2027 internships from the [SimplifyJobs list](https://github.com/SimplifyJobs/Summer2027-Internships) into Supabase.
2. Postings get skill tags and a vector for each description.
3. When you upload a resume, the API turns it into a vector and finds the closest postings.
4. Each match is scored: `fit = 0.6 × meaning match + 0.4 × skill overlap`.

Your resume is read in memory and never saved.

## Repo layout

```
db/          SQL for the database tables
loaders/     Python jobs that fill the database
api/         FastAPI matching API (coming)
web/         Next.js site (coming)
```

## Run the loader

```bash
cp .env.example .env          # then paste your Supabase connection string
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r loaders/requirements.txt
python loaders/load_postings.py
```

## Credits

Job data comes from the [SimplifyJobs Summer 2027 list](https://github.com/SimplifyJobs/Summer2027-Internships). Every result links back to the original posting.
