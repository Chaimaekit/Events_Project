from elasticsearch import Elasticsearch
import os
from dotenv import load_dotenv

load_dotenv()

CLOUD_ID = os.getenv("CLOUD_ID")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")

def get_es_client():
    return Elasticsearch(
        cloud_id=CLOUD_ID,
        basic_auth=("elastic", f"{ELASTIC_PASSWORD}")
        )