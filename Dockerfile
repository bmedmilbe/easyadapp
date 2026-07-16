FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 1. Install build tools required to compile psycopg2-binary
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Upgrade pip to ensure the best compatibility with pre-built wheels
RUN pip install --no-cache-dir --upgrade pip pipenv

COPY Pipfile ./

RUN pipenv install --system --skip-lock

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
