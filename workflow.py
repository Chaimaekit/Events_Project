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
    insert_casa_events()
    insert_event_brit()
    insert_events_ma()
    insert_guichet()

if __name__ == "__main__":
    print_events()