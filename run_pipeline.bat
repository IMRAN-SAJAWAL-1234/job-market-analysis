@echo off
cd /d E:\job-market-analysis
if not exist logs mkdir logs
E:\job-market-analysis\venv\Scripts\python.exe pipeline.py %* >> logs\scheduler.log 2>&1