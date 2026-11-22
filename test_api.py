import os
import requests
from dotenv import load_dotenv

load_dotenv()

url = "https://api.adzuna.com/v1/api/jobs/sg/search/1"
params = {
    "app_id": os.getenv("ADZUNA_APP_ID"),
    "app_key": os.getenv("ADZUNA_APP_KEY"),
    "what": "data analyst",
    "results_per_page": 5,
    "content-type": "application/json",
}

response = requests.get(url, params=params, timeout=30)
print("Status:", response.status_code)

data = response.json()
print("Total matching jobs:", data.get("count"))
print("Keys in first job:", list(data["results"][0].keys()))
print(data["results"][0]["title"], "|", data["results"][0]["company"]["display_name"])
