import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

from load import JOB_COLS   # same column list as the SQLite loader

load_dotenv()
PROCESSED = Path("data/processed")

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    job_title TEXT,
    job_title_short TEXT,
    company_name TEXT,
    job_location TEXT,
    job_country TEXT,
    category TEXT,
    contract_time TEXT,
    description TEXT,
    job_posted_date TIMESTAMPTZ,
    salary_min DOUBLE PRECISION,
    salary_max DOUBLE PRECISION,
    salary_avg DOUBLE PRECISION,
    salary_currency TEXT,
    salary_is_predicted BOOLEAN,
    salary_status TEXT,
    possible_repost BOOLEAN,
    extracted_at TIMESTAMPTZ,
    source_file TEXT
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_id TEXT NOT NULL REFERENCES jobs (job_id),
    skill TEXT NOT NULL,
    PRIMARY KEY (job_id, skill)
);

CREATE INDEX IF NOT EXISTS idx_jobs_posted ON jobs (job_posted_date);
CREATE INDEX IF NOT EXISTS idx_jobs_role ON jobs (job_title_short);
"""


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def to_records(df):
    """DataFrame -> list of plain tuples, with NaN turned into None (SQL NULL)."""
    df = df.copy()
    for col in ("salary_is_predicted", "possible_repost"):
        df[col] = df[col].astype(str).str.lower().isin(["true", "1"])
    df = df.astype(object).where(df.notna(), None)
    return list(df[JOB_COLS].itertuples(index=False, name=None))


def load(jobs, skills):
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in JOB_COLS if c != "job_id")
    upsert_jobs = (
        f"INSERT INTO jobs ({', '.join(JOB_COLS)}) VALUES %s "
        f"ON CONFLICT (job_id) DO UPDATE SET {updates}"
    )
    skill_rows = list(skills[["job_id", "skill"]].itertuples(index=False, name=None))

    conn = get_connection()
    try:
        with conn:                       # one transaction: commit, or roll back on error
            with conn.cursor() as cur:
                cur.execute(SCHEMA)
                execute_values(cur, upsert_jobs, to_records(jobs), page_size=500)

                # replace skills for these jobs so re-runs never leave stale rows
                cur.execute(
                    "DELETE FROM job_skills WHERE job_id = ANY(%s)",
                    (list(jobs["job_id"]),),
                )
                if skill_rows:
                    execute_values(
                        cur,
                        "INSERT INTO job_skills (job_id, skill) VALUES %s "
                        "ON CONFLICT DO NOTHING",
                        skill_rows,
                    )

                cur.execute("SELECT COUNT(*) FROM jobs")
                n_jobs = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM job_skills")
                n_skills = cur.fetchone()[0]
    finally:
        conn.close()
    print(f"PostgreSQL warehouse now holds {n_jobs} jobs and {n_skills} job-skill rows")


if __name__ == "__main__":
    jobs = pd.read_csv(PROCESSED / "jobs_clean.csv", dtype={"job_id": str})
    skills = pd.read_csv(PROCESSED / "job_skills_clean.csv", dtype={"job_id": str})
    load(jobs, skills)