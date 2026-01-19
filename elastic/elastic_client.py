from elasticsearch import Elasticsearch
import os
from dotenv import load_dotenv

load_dotenv()

def get_es_client(use_docker=False) -> Elasticsearch:
    
    if use_docker or os.getenv("ELASTICSEARCH_HOST"):
        elasticsearch_host = os.getenv("ELASTICSEARCH_HOST", "")
        elasticsearch_user = os.getenv("ELASTICSEARCH_USER", "")
        elasticsearch_password = os.getenv("ELASTIC_PASSWORD", "")
        
        print(f"Connecting to local Elasticsearch at {elasticsearch_host}")
        return Elasticsearch(
            [elasticsearch_host],
            basic_auth=(elasticsearch_user, elasticsearch_password) if elasticsearch_password else None
        )
    
    cloud_id = os.getenv("CLOUD_ID")
    elastic_password = os.getenv("ELASTIC_PASSWORD")

    if not cloud_id:
        raise RuntimeError("CLOUD_ID is not set")
    if not elastic_password:
        raise RuntimeError("ELASTIC_PASSWORD is not set")

    print(f"Connecting to Elastic Cloud")
    return Elasticsearch(
        cloud_id=cloud_id,
        basic_auth=("elastic", elastic_password),
    )