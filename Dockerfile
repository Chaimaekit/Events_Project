FROM prefecthq/prefect:2-python3.12

WORKDIR /opt/prefect/flows

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Optionally copy your full repo, comment this if you rely on git_clone pull step
# COPY . /opt/prefect/flows
