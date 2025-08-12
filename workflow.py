from prefect import flow, task
from scrape.casaevents import get_casa_events
from scrape.eventbrit import get_event_brit
from scrape.eventsma import get_events_ma
from scrape.guichet import get_guichet
from into_db.connection import insert_events

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

@flow
def print_events():
    first_event = insert_casa_events().submit()
    second_event = insert_event_brit().submit(wait_for=[first_event])
    third_event = insert_events_ma().submit(wait_for=[second_event])
    forth_event = insert_guichet().submit(wait_for=[third_event])
    print(forth_event)

if __name__ == "__main__":
     print_events.deploy(
        name="print-events",
        work_pool_name="my-process-pool",
        image="chaimaaeljerrar/scraping-image:latest",  # image with your code
        push=True,
        cron="*/2 * * * *",  # every 2 minutes
    )