from prefect import flow, task
from scrape.casaevents import get_casa_events
from scrape.eventbrit import get_event_brit
from scrape.eventsma import get_events_ma
from scrape.guichet import get_guichet
from into_db.connection import insert_events
import time
from dotenv import load_dotenv
import os

load_dotenv()
username = os.getenv("DOCKER_USERNAME")

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
    first_event = insert_casa_events()
    time.sleep(5)
    second_event = insert_event_brit()
    time.sleep(5)
    third_event = insert_events_ma()
    time.sleep(5)
    forth_event = insert_guichet()
    print(forth_event)

if __name__ == "__main__":
     print_events.deploy(
        name="print-events",
        work_pool_name="my-process-pool",
        image=f"{username}/scraping-image:latest", 
        push=True,
        cron="*/2 * * * *",
    )