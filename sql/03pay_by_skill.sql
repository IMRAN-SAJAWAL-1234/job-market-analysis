query = """
SELECT s.skill,
       COUNT(*) AS postings,
       ROUND(AVG(j.salary_year_avg), 0) AS avg_salary
FROM jobs j
JOIN job_skills s ON s.job_id = j.job_id
WHERE j.job_title_short = 'Data Analyst'
  AND j.job_country = 'United States'
  AND j.salary_year_avg IS NOT NULL
GROUP BY s.skill
HAVING COUNT(*) >= 50
ORDER BY avg_salary DESC
LIMIT 10;
"""
pd.read_sql(query, conn)