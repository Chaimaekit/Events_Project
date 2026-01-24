from elasticsearch import Elasticsearch, helpers
from into_db.connection import get_db_events
from scrape.casaevents import get_casa_events
from scrape.eventbrit import get_event_brit
from scrape.eventsma import get_events_ma
from scrape.guichet import get_guichet
import hashlib
from elastic.elastic_client import get_es_client
import logging
import os


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
use_docker = os.getenv("ELASTICSEARCH_HOST") is not None
es = get_es_client(use_docker=use_docker)
INDEX_NAME = "events_index"


def indexing():
    try:
        logger.info("starting the indexing process ------")
        logger.info("testing Elasticsearch connection--------")
        if not es.ping():
            logger.error("cant connect to Elasticsearch !!!")
            return False
        logger.info("connected to Elasticsearch --------")

        index_exists = es.indices.exists(index=INDEX_NAME)
        logger.info(f"'{INDEX_NAME}' exists: {index_exists}")
        
        if not index_exists:
            logger.info(f"creating index '{INDEX_NAME}' !!!!")
            es.indices.create(index=INDEX_NAME)
            logger.info(f"index '{INDEX_NAME}' created...")
        else:
            logger.info(f"index '{INDEX_NAME}' already exists")

        logger.info("fetching events from all sources...")
        events = []
        events.extend(get_casa_events())
        logger.info(f"Casa Events: {len(events)} events")
        events.extend(get_event_brit())
        logger.info(f"EventBrit: {len(events) - len(get_casa_events())} events")
        events.extend(get_events_ma())
        logger.info(f"EventsMa: {len(events)} total events")
        events.extend(get_guichet())
        logger.info(f"Total events collected: {len(events)}")

        if not events:
            logger.warning("No events collected from any source")
            return False

        logger.info("Fetching existing event URLs...")
        try:
            existing_urls = set()
            existing_response = es.search(
                index=INDEX_NAME,
                query={"match_all": {}},
                size=10000,
                _source=["url"]
            )
            for hit in existing_response["hits"]["hits"]:
                url = hit["_source"].get("url", "")
                if url:
                    existing_urls.add(url)
            logger.info(f"Found {len(existing_urls)} existing event URLs")
        except Exception as e:
            logger.warning(f"Could not fetch existing URLs: {str(e)}")
            existing_urls = set()

        logger.info("Preparing bulk actions...")
        actions = []
        skipped = 0
        
        for event in events:
            event_url = event.get("url", "")
            
            #skip the event if its url already exists(unique)
            if event_url in existing_urls:
                skipped += 1
                continue
            
            doc_id = hashlib.md5(
                (str(event.get("name", "")) + str(event.get("date", "")) + str(event.get("city", ""))).encode()
            ).hexdigest()

            doc = {
                "id": event.get("id", ""),
                "name": event.get("name", ""),
                "img": event.get("img", ""),
                "description": event.get("description", ""),
                "date": event.get("date", {}),
                "city": event.get("city", ""),
                "place": event.get("place", ""),
                "location": event.get("city", "") + " " + event.get("place", ""),
                "producer": event.get("producer", ""),
                "category": event.get("category", []),
                "offers": event.get("offers", []),
                "url": event.get("url", "")
            }

            actions.append({
                "_op_type": "index",
                "_index": INDEX_NAME,
                "_id": doc_id,
                "_source": doc
            })
        
        logger.info(f"Total actions prepared: {len(actions)} (skipped {skipped} duplicates)")

        if actions:
            logger.info("Starting bulk indexing...")
            success, failed = helpers.bulk(es, actions, raise_on_error=False)
            logger.info(f"{success} events indexed successfully!")
            if failed:
                logger.warning(f"✗ {failed} events failed to index")
                return success > 0
            return True
        else:
            logger.warning("No events to index.")
            return False
            
    except Exception as e:
        logger.error(f"Error during indexing: {str(e)}", exc_info=True)
        return False


def check_doc(index_name, event_name):
    try:
        result = es.search(
            index=index_name,
            query={"match": {"name": event_name}},
            size=20
        )
        return result["hits"]["hits"] if result else []
    except Exception as e:
        logger.error(f"Error checking documents: {str(e)}", exc_info=True)
        return []


if __name__ == "__main__":
    success = indexing()
    if success:
        logger.info("indexing completed successfully")
    else:
        logger.error("indexing failed or found no events")
