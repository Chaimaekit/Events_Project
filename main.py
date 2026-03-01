from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from elastic.elastic_client import get_es_client
from transport.bus import lignes_casabus, load_casabus_stops, calculate_casabus_lignes, stations_to_lines, haversine
from datetime import datetime
from contextlib import asynccontextmanager
from elastic_script import indexing
import asyncio
from scipy.spatial import KDTree
import numpy as np



@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(asyncio.to_thread(indexing))
    yield


try:
    load_casabus_stops()
    calculate_casabus_lignes()
    stations_to_lines()
    print("Transport data loaded successfully")
except Exception as e:
    print(f"Warning: Transport data not loaded: {e}")

try:
    es = get_es_client()
except Exception as e:
    print(f"Warning: Elasticsearch client not created at startup: {e}")
    es = None
app = FastAPI(title="Evently API", version="1.0.0", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


all_stop_coords = []
all_stop_lines = []

for ligne in lignes_casabus:
    for point in ligne["coordinates"]:
        all_stop_coords.append([point[0], point[1]])
        all_stop_lines.append(ligne)
stop_tree = KDTree(np.array(all_stop_coords))



# @app.get("/startup")
# async def startup_event():
#     try:
#         from elastic_script import indexing
#         success = indexing()
#         if success:
#             print("Events indexed successfully at startup")
#         else:
#             print("No events were indexed at startup")
#     except Exception as e:
#         print(f"Error during startup indexing: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/debug/dates")
async def debug_dates():
    """Debug endpoint to check dates in index"""
    response = es.search(
        index="events_index",
        query={"match_all": {}},
        size=5
    )
    dates = []
    for hit in response["hits"]["hits"]:
        if hit["_source"].get("date"):
            dates.append(hit["_source"]["date"])
    return {"sample_dates": dates[:3]}

@app.get("/reindex")
async def reindex_events():
    """Clear and reindex all events"""
    try:
        if not es:
            raise RuntimeError("Elasticsearch client is not initialized")
        if es.indices.exists(index="events_index"):
            es.indices.delete(index="events_index")
            print("Deleted existing index")
        from elastic_script import indexing
        success = indexing()
        return {"status": "reindexing complete", "success": success}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def get_transport_info(event_coords, threshold_km=0.5):
    transport_info = {
        "bus_lines": [],
        "tramway_info": None
    }

    if not event_coords or len(event_coords) < 2:
        return transport_info

    event_lon, event_lat = event_coords[0], event_coords[1]
    indices = stop_tree.query_ball_point([event_lon, event_lat], r=threshold_km / 111)

    seen_lines = set()
    unique_lines = []

    for i in indices:
        ligne = all_stop_lines[i]
        ligne_nb = ligne["ligne_nb"]
        if ligne_nb not in seen_lines:
            unique_lines.append({
                "ligne_nb": ligne_nb,
                "start": ligne["start"],
                "end": ligne["end"],
            })
            seen_lines.add(ligne_nb)
            if len(unique_lines) >= 3:
                break

    transport_info["bus_lines"] = unique_lines
    return transport_info

@app.get("/transport/{event_id}")
async def get_event_transport(event_id: str):
    """Get transport information for a specific event"""
    try:
        response = es.search(
            index="events_index",
            query={"term": {"id.keyword": event_id}}
        )
        
        if response["hits"]["hits"]:
            event = response["hits"]["hits"][0]["_source"]
            coords = event.get("coordinates")
            transport_info = get_transport_info(coords)
            return transport_info
        else:
            raise HTTPException(status_code=404, detail="Event not found")
    except Exception as e:
        return JSONResponse({"error": str(e), "bus_lines": [], "tramway_info": None}, status_code=500)

@app.get("/search")
async def search_events(
    q: str = Query("", description="Search query"),
    city: str = Query("", description="Filter by city"),
    category: str = Query("", description="Filter by category"),
    date: str = Query("", description="Filter by date (YYYY-MM-DD)"),
    upcoming: bool = Query(False, description="Show only upcoming events"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(12, ge=1, le=100, description="Items per page"),
    sort: str = Query("date_asc", description="Sort order: date_asc, date_desc, popular")
):
    try:
        start = (page - 1) * size
        must_clauses = []
        filter_clauses = []

        if q.strip():
            must_clauses.append({
                "multi_match": {
                    "query": q,
                    "fields": ["name^3", "description^2", "producer", "place"]
                }
            })

        if city.strip():
            filter_clauses.append({"term": {"city.keyword": city}})
        
        if category.strip():
            filter_clauses.append({"term": {"category.keyword": category}})
        
        if date.strip():
            filter_clauses.append({
                "range": {
                    "date.startAt": {
                        "gte": date + " 00:00:00",
                        "lte": date + " 23:59:59"
                    }
                }
            })
        query_body = {
            "bool": {
                "must": must_clauses if must_clauses else [{"match_all": {}}],
                "filter": filter_clauses
            }
        }
        
        if upcoming:
            today = datetime.now().strftime("%Y-%m-%d") + " 00:00:00"
            query_body["bool"]["must_not"] = {
                "range": {
                    "date.startAt": {
                        "lt": today
                    }
                }
            }

        query = query_body

        response = es.search(
            index="events_index",
            query=query,
            from_=start,
            size=size
        )

        events = [hit["_source"] for hit in response["hits"]["hits"]]
        total = response["hits"]["total"]["value"]

        return {
            "events": events,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
            "query": q,
            "filters": {"city": city, "category": category, "date": date, "upcoming": upcoming}
        }

    except Exception as e:
        import logging
        logging.error(f"Search error: {str(e)}")
        return JSONResponse({"error": str(e), "events": [], "total": 0}, status_code=500)

@app.get("/events")
async def get_all_events(
    page: int = Query(1, ge=1),
    size: int = Query(12, ge=1, le=100),
    sort: str = Query("date_desc")
):
    try:
        start = (page - 1) * size
        
        sort_map = {
            "date_asc": [{"date.startAt": {"order": "asc"}}],
            "date_desc": [{"date.startAt": {"order": "desc"}}],
            "popular": [{"offers": {"order": "desc"}}]
        }

        response = es.search(
            index="events_index",
            query={"match_all": {}},
            from_=start,
            size=size,
            sort=sort_map.get(sort, sort_map["date_desc"])
        )

        events = [hit["_source"] for hit in response["hits"]["hits"]]
        total = response["hits"]["total"]["value"]

        return {
            "events": events,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }

    except Exception as e:
        return JSONResponse({"error": str(e), "events": [], "total": 0}, status_code=500)

@app.get("/event/{event_id}")
async def get_event_detail(event_id: str):
    try:
        response = es.search(
            index="events_index",
            query={"term": {"id.keyword": event_id}}
        )
        
        if response["hits"]["hits"]:
            event = response["hits"]["hits"][0]["_source"]
            return event
        else:
            raise HTTPException(status_code=404, detail="Event not found")
            
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/filters")
async def get_filter_options():
    try:
        cities_response = es.search(
            index="events_index",
            aggs={"cities": {"terms": {"field": "city.keyword", "size": 100}}},
            size=0
        )
        cities = sorted([bucket["key"] for bucket in cities_response["aggregations"]["cities"]["buckets"]])

        categories_response = es.search(
            index="events_index",
            aggs={"categories": {"terms": {"field": "category.keyword", "size": 100}}},
            size=0
        )
        categories = sorted([bucket["key"] for bucket in categories_response["aggregations"]["categories"]["buckets"]])

        return {
            "cities": cities,
            "categories": categories
        }

    except Exception as e:
        return JSONResponse({"error": str(e), "cities": [], "categories": []}, status_code=500)

@app.get("/stats")
async def get_statistics():
    try:
        response = es.search(
        index="events_index",
        query={"match_all": {}},
        aggs={
                "cities": {"terms": {"field": "city.keyword", "size": 10}},
                "categories": {"terms": {"field": "category.keyword", "size": 10}},
                "upcoming": {"filter": {"range": {"date.startAt": {"gte": "now", "lte": "now+7d"}}}}
            },
        size=0
        )
        total_events = response["hits"]["total"]["value"]
        upcoming_count = response["aggregations"]["upcoming"]["doc_count"]
        cities_stats = response["aggregations"]["cities"]["buckets"]
        categories_stats = response["aggregations"]["categories"]["buckets"]
        return {
            "total_events": total_events,
            "upcoming_events": upcoming_count,
            "cities": cities_stats,
            "categories": categories_stats
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    

favorites_store = {}

@app.post("/favorites/{event_id}")
async def add_favorite(event_id: str, user_id: str = Query("guest")):
    if user_id not in favorites_store:
        favorites_store[user_id] = set()
    favorites_store[user_id].add(event_id)
    return {"status": "added", "event_id": event_id}

@app.delete("/favorites/{event_id}")
async def remove_favorite(event_id: str, user_id: str = Query("guest")):
    
    if user_id in favorites_store:
        favorites_store[user_id].discard(event_id)
    return {"status": "removed", "event_id": event_id}

@app.get("/favorites")
async def get_favorites(user_id: str = Query("guest")):
    
    try:
        event_ids = list(favorites_store.get(user_id, set()))
        
        if not event_ids:
            return {"favorites": [], "count": 0}
        
        response = es.search(
            index="events_index",
            query={"terms": {"id.keyword": event_ids}},
            size=100
        )
        
        events = [hit["_source"] for hit in response["hits"]["hits"]]
        return {"favorites": events, "count": len(events)}
        
    except Exception as e:
        return JSONResponse({"error": str(e), "favorites": [], "count": 0}, status_code=500)


@app.get("/calendar")
async def get_calendar_events(month: int = Query(1), year: int = Query(2026)):
    try:
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
        
        response = es.search(
            index="events_index",
            query={
                "range": {
                    "date.startAt": {
                        "gte": start_date,
                        "lt": end_date
                    }
                }
            },
            size=1000
        )
        
        events_by_date = {}
        for hit in response["hits"]["hits"]:
            event = hit["_source"]
            date_key = event.get("date", {}).get("startAt", "").split("T")[0]
            if date_key:
                if date_key not in events_by_date:
                    events_by_date[date_key] = []
                events_by_date[date_key].append(event)
        
        return {
            "month": month,
            "year": year,
            "events": events_by_date
        }
        
    except Exception as e:
        return JSONResponse({"error": str(e), "events": {}}, status_code=500)


@app.get("/recommendations")
async def get_recommendations(event_id: str = Query("")):
    """Get recommended events based on similar events"""
    try:
        if event_id:
            event_response = es.search(
                index="events_index",
                query={"term": {"id.keyword": event_id}},
                size=1
            )
            
            if not event_response["hits"]["hits"]:
                raise HTTPException(status_code=404, detail="Event not found")
            
            event = event_response["hits"]["hits"][0]["_source"]
            category = event.get("category", [""])[0]
            city = event.get("city", "")
        else:
            category = ""
            city = ""
        
        filter_clauses = []
        if category:
            filter_clauses.append({"term": {"category.keyword": category}})
        if city:
            filter_clauses.append({"term": {"city.keyword": city}})
        
        response = es.search(
            index="events_index",
            query={
                "bool": {
                    "filter": filter_clauses if filter_clauses else [{"match_all": {}}],
                    "must_not": [{"term": {"id.keyword": event_id}}] if event_id else []
                }
            },
            size=6
        )
        
        events = [hit["_source"] for hit in response["hits"]["hits"]]
        return {"recommendations": events}
        
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse({"error": str(e), "recommendations": []}, status_code=500)


@app.get("/trending")
async def get_trending_events():
    try:
        response = es.search(
            index="events_index",
            query={
                "range": {
                    "date.startAt": {
                        "gte": "now"
                    }
                }
            },
            sort=[{"offers": {"order": "desc"}}],
            size=10
        )
        
        events = [hit["_source"] for hit in response["hits"]["hits"]]
        return {"trending": events}
        
    except Exception as e:
        return JSONResponse({"error": str(e), "trending": []}, status_code=500)


@app.post("/export")
async def export_events(format: str = Query("json")):
    try:
        response = es.search(
            index="events_index",
            query={"match_all": {}},
            size=1000
        )
        
        events = [hit["_source"] for hit in response["hits"]["hits"]]
        
        if format == "csv":
            csv_data = "name,city,date,category,url\n"
            for event in events:
                csv_data += f"\"{event.get('name', '')}\",\"{event.get('city', '')}\",\"{event.get('date', {}).get('startAt', '')}\",\"{event.get('category', [''])[0]}\",\"{event.get('url', '')}\"\n"
            return JSONResponse({"csv": csv_data})
        else:
            return {"events": events}
            
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/health")
async def health_check():
    try:
        es.info()
        return {"status": "healthy", "elasticsearch": "connected"}
    except Exception as e:
        return JSONResponse({"status": "unhealthy", "error": str(e)}, status_code=500)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

