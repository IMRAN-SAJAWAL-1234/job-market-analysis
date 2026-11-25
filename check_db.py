# import sqlite3, pandas as pd
# conn = sqlite3.connect("data/warehouse.db")
# print(pd.read_sql("SELECT job_title_short, COUNT(*) AS jobs FROM jobs GROUP BY job_title_short ORDER BY jobs DESC", conn))
# print(pd.read_sql("SELECT skill, COUNT(*) AS jobs FROM job_skills GROUP BY skill ORDER BY jobs DESC LIMIT 10", conn))
# print(pd.read_sql("SELECT SUM(possible_repost) AS reposts, COUNT(*) AS total FROM jobs", conn))
# print(pd.read_sql("SELECT MIN(job_posted_date) AS oldest, MAX(job_posted_date) AS newest FROM jobs", conn))
# conn.close()

# import sqlite3, pandas as pd
# conn = sqlite3.connect("data/warehouse.db")

# print(pd.read_sql("""
#     SELECT
#       CASE
#         WHEN julianday('now') - julianday(job_posted_date) <= 30  THEN '1: last 30 days'
#         WHEN julianday('now') - julianday(job_posted_date) <= 90  THEN '2: 31-90 days'
#         WHEN julianday('now') - julianday(job_posted_date) <= 365 THEN '3: 91-365 days'
#         ELSE '4: over a year'
#       END AS age_bucket,
#       COUNT(*) AS jobs
#     FROM jobs GROUP BY age_bucket ORDER BY age_bucket
# """, conn))

# print(pd.read_sql("""
#     SELECT job_title, company_name, job_posted_date
#     FROM jobs WHERE job_title_short = 'Other' LIMIT 10
# """, conn))
# conn.close()

import extract

url = "https://api.adzuna.com/v1/api/jobs/sg/search/1"
params = {
    "app_id": extract.APP_ID,
    "app_key": extract.APP_KEY,
    "what": "data analyst",
    "results_per_page": 20,
    "max_days_old": 30,
}
r = extract.get_with_retry(url, params)
dates = sorted(j["created"] for j in r.json()["results"])
print(dates[0], "to", dates[-1])