-- Part 1: job tables. Already run in Supabase on Oct 12, 2026.
-- Keep this file so the schema lives in the repo.

create extension if not exists vector;

create table postings (
  id           text primary key,  -- the list's own id
  company      text not null,
  title        text not null,
  url          text not null,
  locations    text[],
  terms        text[],
  category     text,              -- the list's role category
  active       boolean,
  date_posted  timestamptz,
  description  text,              -- null when no public description
  skills       text[],            -- tagged by the loader
  embedding    vector(384),
  updated_at   timestamptz default now()
);

create table skills (
  name    text primary key,       -- 'python', 'react', 'pytorch'
  aliases text[],                 -- 'py', 'reactjs'
  kind    text                    -- 'language', 'framework', 'tool', 'concept'
);

create table eval_cases (
  id       serial primary key,
  kind     text,                  -- 'job' or 'course'
  query    text,
  expected text[]                 -- ids that should rank near the top
);

-- Block Supabase's public API. The loaders and API connect directly.
alter table postings   enable row level security;
alter table skills     enable row level security;
alter table eval_cases enable row level security;
