from prefect import flow, task
from scrape.casaevents import get_casa_events
from scrape.eventbrit import get_event_brit
from scrape.eventsma import get_events_ma
from scrape.guichet import get_guichet
from into_db.connection import insert_events

@task
def insert_casa_events():
    events = get_casa_events()
    if events:
        insert_events(events)

@task
def insert_event_brit():
    events = get_event_brit()
    if events:
        insert_events(events)

@task
def insert_events_ma():
    events = get_events_ma()
    if events:
        insert_events(events)
    return events

@task
def insert_guichet():
    events = get_guichet()
    if events:
        insert_events(events)

@flow
def print_events():
    first_event = insert_casa_events()
    second_event = insert_event_brit()
    third_event = insert_events_ma()
    forth_event = insert_guichet()
    print(third_event)

if __name__ == "__main__":
    print_events.deploy(
        name="scraper",
        work_pool_name="default",
        image="chaimaaeljerrar/scraping-image:latest",
        push=False,
        cron="*/2 * * * *",
    )