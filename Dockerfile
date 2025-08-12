# Start from an official Prefect image
FROM prefecthq/prefect:3-python3.12

# Install system deps (optional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy your code (optional — if you rely on git clone in pull_steps, you don’t have to copy here)
# COPY . /opt/prefect/flows

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Optional: Set working directory
WORKDIR /opt/prefect/flows
