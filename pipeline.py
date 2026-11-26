import argparse
import logging
import sys
from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()

import pandas as pd

import extract
import load
import transform

COUNTRY = "sg"
QUERIES = ["data analyst", "data engineer", "data scientist"]
PAGES = 2   # 3 queries x 2 pages = 6 API calls per run

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("pipeline")


def check_quality(jobs, skills):
    """Return (errors, warnings). Errors stop the load; warnings are logged."""
    errors, warnings = [], []

    if len(jobs) == 0:
        errors.append("no jobs after transform")
    if jobs["job_id"].isna().any():
        errors.append("null job_id found")
    if not jobs["job_id"].is_unique:
        errors.append("duplicate job_id found")
    if jobs["job_posted_date"].isna().mean() > 0.05:
        errors.append("more than 5% of posted dates failed to parse")

    if (jobs["job_posted_date"] > pd.Timestamp.now(tz="UTC")).any():
        errors.append("posted dates in the future")

    if set(skills["job_id"]) - set(jobs["job_id"]):
        errors.append("skills reference jobs that don't exist")

    if (jobs["job_title_short"] == "Other").mean() > 0.5:
        warnings.append("over half of titles fell into 'Other'; check the role rules")
    sal = jobs["salary_avg"].dropna()
    if len(sal) > 1 and sal.max() / sal.min() > 20:
        warnings.append(
            f"salary scale inconsistent (min {sal.min():.0f}, max {sal.max():.0f}); "
            "kept as 'unverified'"
        )
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=90)
    old_share = (jobs["job_posted_date"] < cutoff).mean()
    if old_share > 0.25:
        warnings.append(f"{old_share:.0%} of jobs are older than 90 days; check search freshness")

    return errors, warnings


def run(skip_extract=False):
    log.info("Pipeline started | country=%s | queries=%s", COUNTRY, QUERIES)

    # 1. Extract
        # 1. Extract
    if skip_extract:
        log.info("Skipping extract (--skip-extract): re-processing saved raw files")
    else:
        saved = 0
        for q in QUERIES:
            try:
                jobs = extract.extract(country=COUNTRY, query=q, pages=PAGES)
                path = extract.save_raw(jobs, COUNTRY, q)
                log.info("Extracted %d jobs for '%s' -> %s", len(jobs), q, path.name)
                saved += 1
            except Exception:
                log.exception("Extract failed for '%s'", q)
        if saved == 0:
            raise RuntimeError("All extractions failed; nothing new to process")

    # 2. Transform (re-reads every raw file, so it is safe to re-run)
    rows = [r for f in sorted(transform.RAW_DIR.glob("adzuna_*.json"))
            for r in transform.load_raw(f)]
    jobs, skills = transform.transform(rows)
    log.info("Transformed %d raw rows into %d unique jobs, %d skill rows",
             len(rows), len(jobs), len(skills))

    # 3. Quality checks
    errors, warnings = check_quality(jobs, skills)
    for w in warnings:
        log.warning(w)
    if errors:
        for e in errors:
            log.error(e)
        raise RuntimeError("Data quality checks failed; nothing was loaded")

    # 4. Load (dates as text so SQLite stores them cleanly)
    for col in ("job_posted_date", "extracted_at"):
        jobs[col] = jobs[col].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    # load.load(jobs, skills)

    
    target = os.getenv("WAREHOUSE", "sqlite").lower()
    if target == "postgres":
        import load_pg          # imported here so SQLite mode doesn't need psycopg2
        load_pg.load(jobs, skills)
    elif target == "sqlite":
        load.load(jobs, skills)
    else:
        raise RuntimeError(f"Unknown WAREHOUSE setting: {target!r}")
    log.info("Loaded into %s", target)
    
    log.info("Pipeline finished OK")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-extract",
        action="store_true",
        help="re-process saved raw files without calling the API",
    )
    args = parser.parse_args()
    try:
        run(skip_extract=args.skip_extract)
    except Exception:
        log.exception("Pipeline failed")
        sys.exit(1)

# if __name__ == "__main__":
#     try:
#         run()
#     except Exception:
#         log.exception("Pipeline failed")
#         sys.exit(1)

