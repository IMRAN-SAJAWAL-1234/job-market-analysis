# Data Job Market Analysis( CV small personal project)

## Goal of the project
In modenr Data field, what skill and roles are in demand. A full project from basic analysis to automated pipeline and predictive model.

## Data
lukebarousse/data_jobs (Hugging Face), real data job postings
with 700000+ rows and 17 columns

https://huggingface.co/datasets/lukebarousse/data_jobs/viewer/default/train


## Tools
Python, pandas, matplotlib/seaborn, Jupyter, SQL, Git


## Info about the loaded dataset
- Salary_year_avg is missing in 97.2% of rows, so only about 3 in 100 postings have a yearly salary.
- Job_skills is missing in only 14.9% of rows, so most postings have skills listed.
- Titles, dates, and countries have 0% missing. job_schedule_type (1.6%) and job_location (0.1%) are minor.
- The US dominates with 206,292 rows (about 26%), followed by India, the UK, France, and Germany.

- Found some row has search_location = Sudan, but the actual job_location values are US cities (Phoenix, Houston, San Francisco) or "Anywhere" (remote). None of these jobs is in Sudan.

Data quality note: job_country reflects the search query, not the job's actual location. About 98% of rows labeled "Sudan" had US or remote locations, so they were excluded from country-level analysis.

A first location-format check flagged the UK, but inspection showed it was a pattern artifact; a stricter check confirmed only Sudan was affected

## Business questions 

- Which skills are most requested for Data Analyst roles globally, and how does Malaysia compare?

- How do the top skills differ between Data Analyst, Data Engineer, and Data Scientist?

  **SQL is the common thread. It's in 58% of Analyst, 67% of Engineer, and 54% of Scientist postings. It's the one skill that pays off whichever way your career goes.

  **Python grows as you move toward engineering and science. It's 36% for Analysts, 64% for Engineers, and 78% for Scientists. It's the second skill to learn, and the one that makes your later stages possible.

  **Excel and BI tools are analyst territory. Excel is 42% for Analysts but only 5% for Engineers and 12% for Scientists. Power BI is 25% for Analysts vs about 11% for the other two. Tableau is also strongest for Analysts (29%).


- How has demand for each role changed over time?
   One year of data (2023) can show seasonality but not trend; the January peak may be a collection artifact

- What share of postings are remote or mention no degree requirement, by role --Eg: in malaysia--?
  **Remote work is rare in Malaysia. Only 1.5-2.7% of core-role postings are flagged as work from home. Local employers mostly want people in the office.
  **Data Scientist postings mention degrees far more often. Only 8.9% don’t mention a degree, vs 32.3% for Analysts and 36.9% for Engineers. A plausible reading is that science roles lean harder on formal qualifications, while analyst and engineer roles are more open to portfolios and skills


SQL results match pandas exactly (SQL at 58.0%, Excel at 41.9%, and so on), cross-checked the analysis two ways.

## Dashboards

![alt text](image.png)

https://public.tableau.com/app/profile/imran.sajawal/viz/Jobanalysis_17948999525800/Dashboard1?publish=yes

## Findings
- SQL appears in 58% of Data Analyst postings, the top skill, and is the only skill that ranks highly for all three roles.
- Python rises from 36% (Analyst) to 64% (Engineer) and 78% (Scientist).
- Cloud and big-data tools (AWS, Azure, Spark) are roughly 5-10x more common in Engineer postings than Analyst ones.
- In Malaysia, Excel is mentioned more often than globally (50% vs 42% of Analyst postings), and remote work is rare (under 3% of core-role postings).
- Limitations: one year of data (2023), country labels reflect the search query (Sudan excluded), salary covers about 3% of postings and is mostly US, “no degree mentioned” doesn’t    mean “no degree required.”


![Dashboard](dashboard/Dashboard%201.png)





Adzuna returns descriptions truncated to ~500 characters, so only 12% of postings had a detectable skill. Skill percentages from the pipeline are lower bounds and are not comparable with the full-description Stage 1 data.