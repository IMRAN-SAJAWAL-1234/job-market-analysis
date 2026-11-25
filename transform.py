import json
import re
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/processed")

CURRENCY = {"sg": "SGD", "gb": "GBP", "us": "USD", "in": "INR"}

# skill name -> regex. \b means "word boundary", so \bsql\b matches "SQL"
# and "T-SQL" but not "MySQL" or "NoSQL".
SKILL_PATTERNS = {
    "sql": r"\bsql\b",
    "python": r"\bpython\b",
    "excel": r"\bexcel\b(?!\s+(?:in|at|as|with|under)\b)",  # skips the verb "excel in"
    "tableau": r"\btableau\b",
    "power bi": r"\bpower\s?bi\b",
    "sas": r"\bsas\b",
    "sap": r"\bsap\b",
    "powerpoint": r"\bpower\s?point\b",
    "looker": r"\blooker\b",
    "qlik": r"\bqlik",
    "alteryx": r"\balteryx\b",
    "aws": r"\baws\b|\bamazon web services\b",
    "azure": r"\bazure\b",
    "gcp": r"\bgcp\b|\bgoogle cloud\b",
    "spark": r"\bspark\b|\bpyspark\b",
    "hadoop": r"\bhadoop\b",
    "kafka": r"\bkafka\b",
    "airflow": r"\bairflow\b",
    "snowflake": r"\bsnowflake\b",
    "databricks": r"\bdatabricks\b",
    "bigquery": r"\bbigquery\b",
    "redshift": r"\bredshift\b",
    "dbt": r"\bdbt\b",
    "java": r"\bjava\b",
    "scala": r"\bscala\b",
    "pandas": r"\bpandas\b",
    "tensorflow": r"\btensorflow\b",
    "git": r"\bgit\b",
    "docker": r"\bdocker\b",
    "jira": r"\bjira\b",
}
COMPILED = {name: re.compile(p, re.IGNORECASE) for name, p in SKILL_PATTERNS.items()}

ROLES = [
    ("data engineer", "Data Engineer"),
    ("data scientist", "Data Scientist"),
    ("data science", "Data Scientist"),
    ("data analyst", "Data Analyst"),
    ("business analyst", "Business Analyst"),
    ("machine learning", "Machine Learning Engineer"),
]
CORE = {"Data Engineer", "Data Scientist", "Data Analyst"}


def classify_title(title):
    t = (title or "").lower()
    for key, label in ROLES:
        if key in t:
            if label in CORE and ("senior" in t or "sr." in t or "sr " in t):
                return f"Senior {label}"
            return label
    return "Other"


def extract_skills(text):
    return [name for name, rx in COMPILED.items() if rx.search(text)]


def load_raw(path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for j in payload["jobs"]:
        rows.append({
            "job_id": str(j.get("id")),
            "job_title": j.get("title"),
            "company_name": (j.get("company") or {}).get("display_name"),
            "job_location": (j.get("location") or {}).get("display_name"),
            "job_country": payload["country"],
            "category": (j.get("category") or {}).get("label"),
            "contract_time": j.get("contract_time"),
            "description": j.get("description"),
            "job_posted_date": j.get("created"),
            "salary_min": j.get("salary_min"),
            "salary_max": j.get("salary_max"),
            "salary_is_predicted": j.get("salary_is_predicted"),
            "extracted_at": payload["extracted_at"],
            "source_file": path.name,
            # redirect_url is deliberately not kept: it embeds the app id
        })
    return rows


def transform(rows):
    df = pd.DataFrame(rows)

    # types
    df["job_posted_date"] = pd.to_datetime(df["job_posted_date"], utc=True, errors="coerce")
    df["extracted_at"] = pd.to_datetime(df["extracted_at"], format="%Y%m%dT%H%M%SZ", utc=True)
    for col in ("salary_min", "salary_max"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["salary_is_predicted"] = df["salary_is_predicted"].astype(str).eq("1")
    df["salary_avg"] = df[["salary_min", "salary_max"]].mean(axis=1)
    df["salary_currency"] = df["job_country"].map(CURRENCY)
    df["salary_status"] = "unverified"

    # derived columns
    df["job_title_short"] = df["job_title"].apply(classify_title)
    text = df["job_title"].fillna("") + " " + df["description"].fillna("")
    df["job_skills"] = text.apply(extract_skills)

    # same job fetched twice -> keep the most recent copy
    df = df.sort_values("extracted_at").drop_duplicates("job_id", keep="last")

    # flag (don't drop) likely reposts: same title + company
    df["possible_repost"] = df.duplicated(subset=["job_title", "company_name"], keep="first")

    skills = (
        df[["job_id", "job_skills"]]
        .explode("job_skills")
        .dropna()
        .rename(columns={"job_skills": "skill"})
    )
    jobs = df.drop(columns=["job_skills"])
    return jobs, skills


def report(rows, jobs, skills):
    n = len(jobs)
    print(f"\nRows in: {len(rows)} | unique jobs: {n}")
    print("Possible reposts flagged:", int(jobs["possible_repost"].sum()))
    print("Description length (chars):")
    print(jobs["description"].str.len().describe().round(0).to_string())
    with_skill = skills["job_id"].nunique()
    print(f"Jobs with at least one skill: {with_skill} ({with_skill / n:.0%})")
    print(f"Average skills per job: {len(skills) / n:.1f}")
    has_sal = jobs["salary_avg"].notna()
    print(f"Jobs with salary: {has_sal.sum()} | of those predicted: "
          f"{int(jobs.loc[has_sal, 'salary_is_predicted'].sum())}")
    print("\nRoles:\n", jobs["job_title_short"].value_counts().to_string())
    print("\nTop skills (% of jobs):")
    print((skills["skill"].value_counts().head(10) / n * 100).round(1).to_string())


if __name__ == "__main__":
    files = sorted(RAW_DIR.glob("adzuna_*.json"))
    if not files:
        raise SystemExit("No raw files found. Run extract.py first.")
    rows = [r for f in files for r in load_raw(f)]
    jobs, skills = transform(rows)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    jobs.to_csv(OUT_DIR / "jobs_clean.csv", index=False)
    skills.to_csv(OUT_DIR / "job_skills_clean.csv", index=False)
    report(rows, jobs, skills)