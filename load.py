import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path("data/warehouse.db")
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
    job_posted_date TEXT,
    salary_min REAL,
    salary_max REAL,
    salary_avg REAL,
    salary_currency TEXT,
    salary_is_predicted INTEGER,
    salary_status TEXT,
    possible_repost INTEGER,
    extracted_at TEXT,
    source_file TEXT
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_id TEXT NOT NULL,
    skill TEXT NOT NULL,
    PRIMARY KEY (job_id, skill),
    FOREIGN KEY (job_id) REFERENCES jobs (job_id)
);
"""

JOB_COLS = [
    "job_id", "job_title", "job_title_short", "company_name", "job_location",
    "job_country", "category", "contract_time", "description", "job_posted_date",
    "salary_min", "salary_max", "salary_avg", "salary_currency",
    "salary_is_predicted","salary_status","possible_repost", "extracted_at", "source_file",
]


def to_records(df):
    """Turn a DataFrame into plain Python rows, with NaN -> None for SQL NULL."""
    df = df.copy()
    for col in ("salary_is_predicted", "possible_repost"):
        df[col] = df[col].astype(int)
    df = df.astype(object).where(df.notna(), None)
    return list(df[JOB_COLS].itertuples(index=False, name=None))


def load(jobs, skills, db_path=DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    placeholders = ",".join("?" for _ in JOB_COLS)
    updates = ",".join(f"{c}=excluded.{c}" for c in JOB_COLS if c != "job_id")
    upsert_jobs = (
        f"INSERT INTO jobs ({','.join(JOB_COLS)}) VALUES ({placeholders}) "
        f"ON CONFLICT(job_id) DO UPDATE SET {updates}"
    )   

    with sqlite3.connect(db_path) as conn:   # one transaction: all or nothing
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA)
        conn.executemany(upsert_jobs, to_records(jobs))

        # replace skills for these jobs so re-runs never leave stale rows
        ids = [(i,) for i in jobs["job_id"]]
        conn.executemany("DELETE FROM job_skills WHERE job_id = ?", ids)
        conn.executemany(
            "INSERT OR IGNORE INTO job_skills (job_id, skill) VALUES (?, ?)",
            list(skills[["job_id", "skill"]].itertuples(index=False, name=None)),
        )

        n_jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        n_skills = conn.execute("SELECT COUNT(*) FROM job_skills").fetchone()[0]
    print(f"Warehouse now holds {n_jobs} jobs and {n_skills} job-skill rows")


if __name__ == "__main__":
    jobs = pd.read_csv(PROCESSED / "jobs_clean.csv", dtype={"job_id": str})
    skills = pd.read_csv(PROCESSED / "job_skills_clean.csv", dtype={"job_id": str})
    load(jobs, skills)
    