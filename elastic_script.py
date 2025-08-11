from elasticsearch import Elasticsearch
from into_db.connection import get_db_events

es = Elasticsearch("http://localhost:9200", verify_certs=False)

def indexing():
    if not es.ping():
        raise ValueError("Connection failed. Make sure Elasticsearch is running.")

    print("Connected to Elasticsearch.")

    events = get_db_events()

    for event in events:
        event.pop("_id")
        es.index(index='events_index', document=event)
        print("Indexing succeded !")

def check_doc(index_name, event):
    result = es.search(index=index_name, body={
        "query": {
            "match":{
                "name":event
            }
        },
        "size": 20 
    })
    if result:
        return result["hits"]["hits"]