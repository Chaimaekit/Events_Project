FROM prefecthq/prefect-client:3-latest

# Install your python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
