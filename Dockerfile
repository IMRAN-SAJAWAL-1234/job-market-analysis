FROM python:3.13-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY requirements-pipeline.txt .
RUN pip install --no-cache-dir -r requirements-pipeline.txt

COPY extract.py transform.py load.py load_pg.py pipeline.py ./

CMD ["python", "pipeline.py"]