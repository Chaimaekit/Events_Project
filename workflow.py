from prefect import flow, task
from scrape.casaevents import get_casa_events
from scrape.eventbrit import get_event_brit
from scrape.eventsma import get_events_ma
from scrape.guichet import get_guichet
from into_db.connection import insert_events
from prefect.futures import wait_for_all

@task
def insert_casa_events():
    return get_casa_events()

@task
def insert_event_brit():
    return get_event_brit()

@task
def insert_events_ma():
    return get_events_ma()

@task
def insert_guichet():
    return get_guichet()

@flow(log_prints=True)
def print_events():
    futures = [
        insert_casa_events().submit(),
        insert_event_brit().submit(),
        insert_events_ma().submit(),
        insert_guichet().submit()
    ]
    wait_for_all(futures)

if __name__ == "__main__":
     print_events.deploy(
        name="print-events",
        work_pool_name="my-process-pool",
        image="chaimaaeljerrar/scraping-image:latest",  # image with your code
        push=True,
        cron="*/2 * * * *",  # every 2 minutes
    )