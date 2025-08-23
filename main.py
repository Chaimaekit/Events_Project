from fastapi import FastAPI, Request, Query
from fastapi.responses import StreamingResponse, JSONResponse
import asyncio
from scrape.casaevents import get_casa_events
from scrape.eventbrit import get_event_brit
from scrape.eventsma import get_events_ma
from scrape.guichet import get_guichet
import uvicorn
from elastic_script import check_doc, indexing
import json
from dotenv import load_dotenv
import os
from elasticsearch import Elasticsearch
import time
from fastapi.responses import FileResponse


load_dotenv()
elastic_password = os.getenv("ELASTIC_PASSWORD")

app = FastAPI()


# async def casa_events_generator():
#     for event in get_casa_events():
#         yield f"Casa Events Data: {event}\n\n"
#         await asyncio.sleep(0.5)

# async def event_brit_generator():
#     for event in get_event_brit():
#         yield f"Eventbrit Data: {event}\n\n"
#         await asyncio.sleep(0.5)

# async def events_ma_generator():
#     for event in get_events_ma():
#         yield f"Events MA Data: {event}\n\n"
#         await asyncio.sleep(0.5)

# async def guichet_generator():
#     for event in get_guichet():
#         yield f"Guichet Data: {event}\n\n"
#         await asyncio.sleep(0.5)

# @app.get("/stream_casa_events")
# async def stream(request: Request):
#     async def event_publisher():
#         async for message in casa_events_generator():
#             if await request.is_disconnected():
#                 break
#             yield message
#     return StreamingResponse(event_publisher(), media_type="text/event-stream")


# @app.get("/stream_event_brit")
# async def stream(request: Request):
#     async def event_publisher():
#         async for message in event_brit_generator():
#             if await request.is_disconnected():
#                 break
#             yield message
#     return StreamingResponse(event_publisher(), media_type="text/event-stream")


# @app.get("/stream_events_ma")
# async def stream(request: Request):
#     async def event_publisher():
#         async for message in events_ma_generator():
#             if await request.is_disconnected():
#                 break
#             if len(message) == 0:
#                 yield{"message":"End of stream !!"}
#                 break
#             yield message
#     return StreamingResponse(event_publisher(), media_type="text/event-stream")


# @app.get("/stream_guichet")
# async def stream(request: Request):
#     async def event_publisher():
#         async for message in guichet_generator():
#             if await request.is_disconnected():
#                 break
#             yield message
#     return StreamingResponse(event_publisher(), media_type="text/event-stream")

# @app.get("/elastic_results")
# def search_event(event_name: str):
#     return JSONResponse(content=check_doc("events_index",event_name), status_code=200)

# @app.get("/normal")
# def get_normal_data():
#     return JSONResponse(content=get_casa_events(), status_code=200)


es = Elasticsearch(
    "http://elasticsearch:9200",
    basic_auth=("elastic", f"{elastic_password}")
)

def event_stream():
   
    try:
        res = es.search(index="events_index", body={"query": {"match_all": {}}, "size": 50})
        events = res.get("hits", {}).get("hits", [])

        for event in events:
            data = {
                "name": event["_source"].get("name", ""),
                "date": event["_source"].get("date", ""),
                "location": event["_source"].get("place", ""),
                "description": event["_source"].get("description", ""),
                "url": event["_source"].get("url", "")
            }
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(0.5) 

    except Exception as e:
        yield f"data: {{'error': '{str(e)}'}}\n\n"

@app.get("/indexing")
def start_indexing():
    try:
        indexing()
        return JSONResponse(content={"message": "Indexing started successfully!"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/")
def root():
    return FileResponse("index.html") 

@app.get("/stream")
def stream():
    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/events")
def get_events(page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=50)):
    start = (page - 1) * size
    try:
        res = es.search(
            index="events_index",
            body={
                "query": {"match_all": {}},
                "from": start,
                "size": size
            }
        )
        events = [
            {
                "name": hit["_source"].get("name", ""),
                "date": hit["_source"].get("date", ""),
                "location": hit["_source"].get("location", ""),
                "description": hit["_source"].get("description", ""),
                "url": hit["_source"].get("url", "")
            }
            for hit in res.get("hits", {}).get("hits", [])
        ]
        total = res["hits"]["total"]["value"]
        return {
            "page": page,
            "size": size,
            "total": total,
            "pages": (total + size - 1) // size,
            "events": events
        }
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
