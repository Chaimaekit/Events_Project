# Evently – Event Scraper + FastAPI + Elasticsearch + GitHub Actions Cron

Evently is a platform that scrapes event data from multiple Moroccan sources, enriches each event with nearby bus and tramway transport info, indexes everything into Elasticsearch, and serves it through a FastAPI backend with a frontend UI.  
All scraping and indexing are automated using GitHub Actions on a scheduled cron job.

---

## 📌 Features

### 🔍 Scraping
- Collects events in parallel from multiple sources (Casaevents, Eventbrite, Events.ma, Guichet)
- Parallel scraping for faster data collection

### 🚌 Transport Integration
- Each event is automatically enriched with nearby **Casabus** and **Tramway** lines at indexing time
- Uses a **KDTree spatial index** for near-instant transport lookups
- Transport data is precomputed and stored directly in the event document — no per-request calculation

### 🧠 Elasticsearch
- Events are indexed with duplicate prevention using hashed unique IDs (MD5)
- Full-text search with filters by city, category, and date
- Aggregations for stats, filters, trending, and recommendations

### ⚡ FastAPI Backend

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Frontend homepage |
| GET | `/events?page=X&size=Y` | Paginated events |
| GET | `/event/{event_id}` | Single event detail |
| GET | `/search` | Search with filters (city, category, date) |
| GET | `/transport/{event_id}` | Bus and tramway lines near an event |
| GET | `/filters` | Available cities and categories |
| GET | `/stats` | Total events, upcoming, cities, categories |
| GET | `/trending` | Trending upcoming events |
| GET | `/recommendations` | Similar events by category and city |
| POST | `/favorites/{event_id}` | Add event to favorites |
| DELETE | `/favorites/{event_id}` | Remove event from favorites |
| GET | `/favorites` | Get favorite events |
| POST | `/export` | Export events as JSON or CSV |
| GET | `/reindex` | Manually trigger full reindex |
| GET | `/health` | Elasticsearch health check |

### 🎨 Frontend
- Dynamic event loading from API
- Pagination, search, and filter support

### 🔄 GitHub Actions Automation
A scheduled workflow runs all scrapers and Elasticsearch indexing automatically on a cron schedule.

---

## 🗂️ Project Structure

```
Events_Project/
│
├── elastic/
│   ├── elastic_script.py     # indexing + transport enrichment
│   └── elastic_client.py     # Elasticsearch client setup
│
├── main.py                   # FastAPI routes + lifespan startup
│
├── static/
│   ├── script.js
│   └── style.css
│
├── templates/
│   └── index.html            # Frontend UI
│
├── requirements.txt
├── .env                      # Environment variables (not committed)
│
├── .github/
│   └── workflows/
│       └── build.yml         # GitHub Actions cron workflow
│
├── Dockerfile
├── docker-compose.yml
│
├── scrape/                   # Scrapers (run in parallel)
│   ├── casaevents.py
│   ├── eventbrit.py
│   ├── eventsma.py
│   └── guichet.py
│
├── struct_events/
│   ├── get_coords.py         # Geocoding utility
│   └── models.py             # Events Pydantic model
│
├── transport/
│   ├── bus.py                # KDTree transport lookup
│   ├── cleaned_lines/
│   └── overpass/
```

---

## ⚙️ Installation & Setup

### 1️⃣ Pull the Docker image OR Clone the repo

```bash
docker pull chaimaaeljerrar/scraping-image:latest
```
OR
```bash
git clone <repo_url>
```

### 2️⃣ (Optional) Create a `.env` file

Only needed if connecting to Elastic Cloud or if security is enabled:

```
ELASTIC_PASSWORD=your_password_here
CLOUD_ID=your_cloud_id_here
```

> When running locally with Docker Compose, Elasticsearch security is disabled by default — no `.env` is required.

### 3️⃣ Build and run the container

```bash
docker compose up
```

The app will:
1. Wait for Elasticsearch to be healthy
2. Automatically start scraping and indexing events in the background
3. Serve the frontend at `http://localhost:8000`

### 4️⃣ Access the app

```
http://localhost:8000
```

---

## 🧪 Testing Locally

```bash
# Check the UI
http://localhost:8000

# Check events API
http://localhost:8000/events

# Check health
http://localhost:8000/health

# Manually trigger reindex
http://localhost:8000/reindex
```

---

## 🔧 How Transport Works

At indexing time, each event's coordinates are used to query a **KDTree** built from all bus and tramway stop coordinates. The nearest lines (within 0.5km) are stored directly on the event document in Elasticsearch.

This means `/transport/{event_id}` is just a simple document read — no spatial computation happens at request time.

---

## 📝 Future Improvements

1. Add infinite scrolling to the frontend
2. Store favorites in Elasticsearch instead of in-memory
3. Add AI-based event deduplication
4. Add user authentication
5. Deploy to cloud with security enabled