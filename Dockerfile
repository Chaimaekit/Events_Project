FROM python:3.10-slim

WORKDIR /app

# Install system dependencies if needed (optional)
# RUN apt-get update && apt-get install -y ...

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Optional: set default command (can be overridden by Prefect infra)
ENTRYPOINT ["prefect"]
