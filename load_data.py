from datasets import load_dataset
import pandas as pd

# Downloading the dataset from Hugging Face
dataset = load_dataset("lukebarousse/data_jobs")
df = dataset["train"].to_pandas()

# Save a local copy so you don't need to re-download
df.to_csv("data_jobs_raw.csv", index=False)

print(df.shape)
print(df.columns.tolist())
print(df.head())