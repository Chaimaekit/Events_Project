FROM prefecthq/prefect:2-python3.12

WORKDIR /opt/prefect/flows

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . /opt/prefect/flows
