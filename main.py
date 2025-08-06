from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
import asyncio
from scrape.casaevents import get_casa_events
from scrape.eventbrit import get_event_brit
from scrape.eventsma import get_events_ma
from scrape.guichet import get_guichet
import uvicorn

app = FastAPI()


# async def casa_events_generator():
#     for event in get_casa_events():
#         yield f"Casa Events Data: {event}\n\n"
#         await asyncio.sleep(0.5)

# async def event_brit_generator():
#     for event in get_event_brit():
#         yield f"Eventbrit Data: {event}\n\n"
#         await asyncio.sleep(0.5)

async def events_ma_generator():
    for event in get_events_ma():
        yield f"Events MA Data: {event}\n\n"
        await asyncio.sleep(0.5)

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


@app.get("/stream_events_ma")
async def stream(request: Request):
    async def event_publisher():
        async for message in events_ma_generator():
            if await request.is_disconnected():
                break
            yield message
    return StreamingResponse(event_publisher(), media_type="text/event-stream")


# @app.get("/stream_guichet")
# async def stream(request: Request):
#     async def event_publisher():
#         async for message in guichet_generator():
#             if await request.is_disconnected():
#                 break
#             yield message
#     return StreamingResponse(event_publisher(), media_type="text/event-stream")

@app.get("/normal")
def get_normal_data():
    return JSONResponse(content=get_casa_events(), status_code=200)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)