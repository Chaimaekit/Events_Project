from elasticsearch import Elasticsearch
from into_db.connection import get_db_events
from scrape.casaevents import get_casa_events
from scrape.eventbrit import get_event_brit
from scrape.eventsma import get_events_ma
from scrape.guichet import get_guichet
from dotenv import load_dotenv
import os
import time



load_dotenv()
elastic_password = os.getenv("ELASTIC_PASSWORD")



def indexing():
    es = Elasticsearch("http://localhost:9200", basic_auth=("elastic", f"{elastic_password}"))
    events = []
    for _ in range(20):
        if es.ping():
            print("Connected to Elasticsearch.")
            break
        print("Waiting for Elasticsearch to be ready...")
        time.sleep(1)
    else:
        raise ValueError("Elasticsearch not available after waiting 20 seconds.")


    es.indices.create(index="events_index", ignore=400)
    casa_events = get_casa_events()
    event_brit = get_event_brit()
    events_ma = get_events_ma()
    guichet = get_guichet()
    events.extend(casa_events)
    events.extend(event_brit)
    events.extend(events_ma)
    events.extend(guichet)
    for event in events:
        doc = {
            "name": event.get("name", ""),
            "date": event.get("date", ""),
            "location": event.get("city", "")+" "+event.get("place", ""),
            "description": event.get("description", ""),
            "url": event.get("url", "")
        }
        es.index(index="events_index", document=doc)
    print("Indexing succeded !")

def check_doc(index_name, event):
    es = Elasticsearch("http://localhost:9200", basic_auth=("elastic", f"{elastic_password}"))
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
    
if __name__ == "__main__":
    indexing()
