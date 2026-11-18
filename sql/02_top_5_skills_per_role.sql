query = """
WITH role_skill AS (
    SELECT j.job_title_short AS role, s.skill, COUNT(*) AS n
    FROM jobs j
    JOIN job_skills s ON s.job_id = j.job_id
    WHERE j.job_title_short IN ('Data Analyst', 'Data Engineer', 'Data Scientist')
    GROUP BY j.job_title_short, s.skill
),
ranked AS (
    SELECT role, skill, n,
           RANK() OVER (PARTITION BY role ORDER BY n DESC) AS rnk
    FROM role_skill
)
SELECT role, rnk, skill, n
FROM ranked
WHERE rnk <= 5
ORDER BY role, rnk;
"""
pd.read_sql(query, conn)