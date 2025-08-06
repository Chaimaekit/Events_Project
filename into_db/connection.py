from pymongo import MongoClient
from struct_events.models import Events

client = MongoClient("mongodb://localhost:27017/")
db = client["mydatabase"]
collection = db["Events"]

def insert_events(events):
    for event in events:
        if not collection.find_one({"url": event["url"]}):
            collection.insert_one(event)
    print("inserted in db !!")