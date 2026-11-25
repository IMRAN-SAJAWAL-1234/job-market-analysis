import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

COUNTRY = "sg"
QUERY = "data analyst"
PAGES = 2            # each page is one API call, so keep this small
PER_PAGE = 50
MAX_DAYS_OLD = 30
RAW_DIR = Path("data/raw")


def get_with_retry(url, params, max_tries=4):
    for attempt in range(1, max_tries + 1):
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            return response
        if response.status_code in (429, 500, 502, 503, 504):
            wait = 2 ** attempt
            print(f"Attempt {attempt}: got {response.status_code}, retrying in {wait}s")
            time.sleep(wait)
        else:
            break
    response.raise_for_status()


def extract(country=COUNTRY, query=QUERY, pages=PAGES):
    if not APP_ID or not APP_KEY:
        raise SystemExit("Missing ADZUNA_APP_ID or ADZUNA_APP_KEY in .env")

    all_jobs = []
    for page in range(1, pages + 1):
        url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
        params = {
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "what": query,
            "results_per_page": PER_PAGE,
            "max_days_old": MAX_DAYS_OLD,
        }
        response = get_with_retry(url, params)
        results = response.json().get("results", [])
        print(f"Page {page}: {len(results)} jobs")
        all_jobs.extend(results)
        if len(results) < PER_PAGE:
            break  # last page reached
        time.sleep(1)  # be polite to the API

    return all_jobs


# if __name__ == "__main__":
#     jobs = extract()
#     RAW_DIR.mkdir(parents=True, exist_ok=True)
#     stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
#     path = RAW_DIR / f"adzuna_{COUNTRY}_{stamp}.json"

#     payload = {
#         "extracted_at": stamp,
#         "country": COUNTRY,
#         "query": QUERY,
#         "jobs": jobs,
#     }
#     path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
#     print(f"Saved {len(jobs)} jobs to {path}")

def save_raw(jobs, country, query):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = query.replace(" ", "_")
    path = RAW_DIR / f"adzuna_{country}_{slug}_{stamp}.json"
    payload = {"extracted_at": stamp, "country": country, "query": query, "jobs": jobs}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


if __name__ == "__main__":
    jobs = extract()
    path = save_raw(jobs, COUNTRY, QUERY)
    print(f"Saved {len(jobs)} jobs to {path}")