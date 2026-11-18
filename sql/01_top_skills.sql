query = """
WITH da AS (
    SELECT DISTINCT j.job_id
    FROM jobs j
    JOIN job_skills s ON s.job_id = j.job_id
    WHERE j.job_title_short = 'Data Analyst'
)
SELECT s.skill,
       COUNT(*) AS postings,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM da), 1) AS pct
FROM job_skills s
JOIN jobs j ON j.job_id = s.job_id
WHERE j.job_title_short = 'Data Analyst'
GROUP BY s.skill
ORDER BY postings DESC
LIMIT 10;
"""
pd.read_sql(query, conn)