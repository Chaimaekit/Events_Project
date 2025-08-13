from elasticsearch import Elasticsearch
from into_db.connection import get_db_events
from scrape.casaevents import get_casa_events
from scrape.eventbrit import get_event_brit
from scrape.eventsma import get_events_ma
from scrape.guichet import get_guichet

es = Elasticsearch("http://localhost:9200", basic_auth=("elastic", "8jfe*MB6Z-9r8PsuVzDs"))

def indexing():
    events = []
    if not es.ping():
        raise ValueError("Connection failed. Make sure Elasticsearch is running.")

    print("Connected to Elasticsearch.")


    for result in get_casa_events():
        events.append(result)
    for result in get_event_brit():
        events.append(result)
    for result in get_events_ma():
        events.append(result)
    for result in get_guichet():
        events.append(result)

    for event in events:
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
    
indexing()