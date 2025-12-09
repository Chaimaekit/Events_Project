from elasticsearch import Elasticsearch, helpers
from into_db.connection import get_db_events
from scrape.casaevents import get_casa_events
from scrape.eventbrit import get_event_brit
from scrape.eventsma import get_events_ma
from scrape.guichet import get_guichet
from dotenv import load_dotenv
import os
import hashlib



load_dotenv()
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")
CLOUD_ID = os.getenv("CLOUD_ID")
INDEX_NAME = "events_index"


def create_es_client():
    return Elasticsearch(
        cloud_id=CLOUD_ID,
        basic_auth=("elastic", f"{ELASTIC_PASSWORD}")
    )


def indexing():
    es = create_es_client()

    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(index=INDEX_NAME)
        print(f"Index '{INDEX_NAME}' created.")

    events = []
    events.extend(get_casa_events())
    events.extend(get_event_brit())
    events.extend(get_events_ma())
    events.extend(get_guichet())

    actions = []
    for event in events:
        doc_id = hashlib.md5(
            (str(event.get("name", "")) + str(event.get("date", "")) + str(event.get("city", ""))).encode()
        ).hexdigest()

        doc = {
            "name": event.get("name", ""),
            "date": event.get("date", ""),
            "location": event.get("city", "") + " " + event.get("place", ""),
            "description": event.get("description", ""),
            "url": event.get("url", "")
        }

        actions.append({
            "_op_type": "index",
            "_index": INDEX_NAME,
            "_id": doc_id,
            "_source": doc
        })
    if actions:
        helpers.bulk(es, actions)
        print(f"{len(actions)} events indexed successfully!")
    else:
        print("No events to index.")


def check_doc(index_name, event_name):
    es = create_es_client()
    result = es.search(
        index=index_name,
        query={"match": {"name": event_name}},
        size=20
    )
    return result["hits"]["hits"] if result else []


if __name__ == "__main__":
    indexing()
