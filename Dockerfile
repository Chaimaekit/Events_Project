# Use Prefect's official image as a base
FROM prefecthq/prefect:2-python3.10

# Set working directory inside the container
WORKDIR /app

# Copy your code into the image
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
