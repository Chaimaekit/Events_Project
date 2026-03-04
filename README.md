# Evently – Event Scraper + FastAPI + Elasticsearch + Airflow / Github Actions

Evently is a platform that scrapes event data from multiple Moroccan sources, geocodes each event venue using **Nominatim (OpenStreetMap)**, enriches each event with nearby bus and tramway transport info, indexes everything into Elasticsearch, and serves it through a FastAPI backend with a frontend UI.

Scraping and indexing are automated on a daily scheduled cron job at midnight, 
with **Slack alerts** on failure.

## Scheduling
- **Apache Airflow** — used for local/self-hosted deployments (runs inside Docker)
- **GitHub Actions** — alternative for cloud deployments using Elastic Cloud

---

## 📌 Features

### 🔍 Scraping
- Collects events in parallel from multiple Moroccan sources
- Parallel scraping for faster data collection

### 📍 Geocoding
- Each event venue is geocoded using the **Nominatim API** (OpenStreetMap) via `geopy`
- Converts venue names and addresses into **coordinates (longitude, latitude)**
- Coordinates are used downstream for transport enrichment via KDTree spatial indexing

### 🚌 Transport Integration
- Each event is automatically enriched with nearby **Casabus** and **Tramway** lines at indexing time
- Uses a **KDTree spatial index** built from precomputed local transport data to find nearest lines
- Transport data is fetched **once** from the **Overpass API** (OpenStreetMap), stored locally as JSON, and reused at every indexing run — no live API calls during the pipeline
- Transport lines are stored directly in the event document — no per-request spatial computation

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
- Search bar with debounce and clear button
- Filters panel: city, category, date, upcoming only, sort
- Grid and list view toggle
- Event detail modal with transport info
- Favorites system with save/remove
- Share events via Twitter, Facebook, WhatsApp, or copy link
- Pagination with ellipsis

### 🔄 Airflow Scheduling
- Daily scraping and indexing triggered automatically at **midnight**
- DAG: `evently_daily_scraping`
- Retries up to **2 times** on failure with a 5 minute delay
- **Slack notifications** on both success and failure
- Airflow UI accessible at `http://localhost:8080`

---

## 🗂️ Project Structure

```
Events_Project/
│
├── elastic/
│   ├── elastic_script.py         # indexing + transport enrichment
│   └── elastic_client.py         # Elasticsearch client setup
│
├── main.py                       # FastAPI routes + lifespan startup
│
├── static/
│   ├── script.js
│   └── style.css
│
├── templates/
│   └── index.html                # Frontend UI
│
├── requirements.txt              # FastAPI app dependencies
├── requirements.airflow.txt      # Airflow container dependencies
├── .env                          # Environment variables (not committed)
│
├── Dockerfile                    # FastAPI container
├── Dockerfile.airflow            # Airflow container with scraping deps
├── docker-compose.yml            # All services
│
├── dags/
│   └── evently_scraping.py       # Airflow DAG — daily scraping pipeline
│
├── scrape/                       # Scrapers (run in parallel)
│   ├── casaevents.py
│   ├── eventbrit.py
│   ├── eventsma.py
│   └── guichet.py
│
├── struct_events/
│   ├── get_coords.py             # Nominatim geocoding (venue → coordinates)
│   └── models.py                 # Events Pydantic model
│
├── transport/
│   ├── bus.py                    # KDTree transport lookup
│   ├── cleaned_lines/            # Preprocessed transport data (JSON)
│   └── overpass/                 # Raw Overpass API data (one-time fetch)
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repo

```bash
git clone <repo_url>
cd Events_Project
```

### 2️⃣ Create a `.env` file

```env
ELASTIC_PASSWORD=your_password_here
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
```

> `SLACK_WEBHOOK_URL` is required for Airflow failure alerts. Get it from https://api.slack.com/apps

### 3️⃣ Build and run all services

```bash
docker compose up --build
```

This will start:
- **Elasticsearch** at `http://localhost:9200`
- **FastAPI** at `http://localhost:8000`
- **Airflow webserver** at `http://localhost:8080`
- **Airflow scheduler** running the daily DAG
- **Postgres** for Airflow metadata (internal)

> Wait about 60 seconds on first run for all services to initialize.

### 4️⃣ Access the app

| Service | URL |
|---------|-----|
| Frontend | http://localhost:8000 |
| Airflow UI | http://localhost:8080 |
| Elasticsearch | http://localhost:9200 |

---

## 🔄 Airflow Setup

### Login to Airflow UI
- URL: `http://localhost:8080`
- Username: `admin`
- Password: `admin123`

### Activate the DAG
1. Find `evently_daily_scraping` in the DAGs list
2. Toggle it **ON** (it's paused by default)
3. Click ▶️ to trigger a manual run first to verify everything works
4. After that it runs automatically every night at **midnight**

### DAG Details

| Property | Value |
|----------|-------|
| DAG ID | `evently_daily_scraping` |
| Schedule | Daily at midnight (`0 0 * * *`) |
| Retries | 2 (5 min delay between retries) |
| Slack alert on success | ✅ |
| Slack alert on failure | ✅ |

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

# Check Airflow
http://localhost:8080
```

---

## 🔧 How the Pipeline Works

```
Scrapers (parallel)
      ↓
Nominatim API — geocode venue name → coordinates
      ↓
KDTree spatial index — coordinates → nearest bus/tramway lines
(from precomputed local JSON, originally fetched from Overpass API)
      ↓
Elasticsearch — event + coordinates + transport lines indexed together
      ↓
FastAPI — serves events, search, filters, transport, favorites
      ↓
Frontend UI — search, modal, pagination, favorites, share
```

At indexing time, each event's venue is geocoded to coordinates, which are used to query a **KDTree** built from all bus and tramway stop coordinates. The nearest lines within 0.5km are stored directly on the event document in Elasticsearch.

This means `/transport/{event_id}` is just a simple document read — no spatial computation or API call happens at request time.

---

## 🐳 Docker Commands Reference

```bash
# First run or after changing Dockerfile/requirements
docker compose up --build

# After changing only Python/JS/HTML files
docker compose up

# Full clean restart (wipes data volumes)
docker compose down -v
docker compose up --build

# View logs for a specific service
docker compose logs airflow-scheduler
docker compose logs fastapi
```

---

## 📝 Future Improvements

1. Add infinite scrolling to the frontend
2. Store favorites in Elasticsearch instead of in-memory
3. Add AI-based event deduplication
4. Add user authentication
5. Deploy to cloud with security enabled
6. Add map view with Leaflet.js
7. Add more Moroccan event sources