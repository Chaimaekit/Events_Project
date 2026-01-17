from elasticsearch import Elasticsearch
import os
from dotenv import load_dotenv #for local testing + requires .env file

load_dotenv()  #loads env vars from .env file for local testing

def get_es_client() -> Elasticsearch:
    cloud_id = os.getenv("CLOUD_ID")
    elastic_password = os.getenv("ELASTIC_PASSWORD")

    if not cloud_id:
        raise RuntimeError("CLOUD_ID is not set")
    if not elastic_password:
        raise RuntimeError("ELASTIC_PASSWORD is not set")

    return Elasticsearch(
        cloud_id=cloud_id,
        basic_auth=("elastic", elastic_password),
    )