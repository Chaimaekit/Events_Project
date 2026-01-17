# Evently – Event Scraper + FastAPI + Elasticsearch + GitHub Actions Cron

Evently is a project that scrapes event data, indexes it into Elasticsearch, and serves it through a FastAPI backend with a front-end UI.  
All scraping and indexing are automated using GitHub Actions on a scheduled cron job.


---

## 📌 Features :

### 🔍 Scraping
- Collects events from multiple sources

### 🧠 Elasticsearch
- Events are indexed
- Prevents duplicates using hashed unique IDs

### ⚡ FastAPI Backend

Endpoints:
- `/` – serves the frontend  
- `/events` – paginated events  
- `/indexing` – manually trigger indexing  
- `/stream` – test server-sent event streaming  

### 🎨 Frontend
- Dynamic event loading from API  
- Pagination support  

### 🔄 GitHub Actions Automation
A scheduled workflow runs:
- All scrapers  
- Elasticsearch indexing script  
- Based on a cron schedule  

---

## 🗂️ Project Structure
```
Events_Project/
│
├── elastic/
│   ├── __init__.py           # exports global 'es' instance
│   └── elastic_client.py     # creates Elasticsearch client
│
├── main.py                   # FastAPI routes
├── elastic_script.py         # indexing script
├── index.html                # Frontend UI
├── requirements.txt
├── .env                      # Environment variables
│
├── .github/
│   └── workflows/
│       └── build.yml         # GitHub Actions cron workflow
│
├── Dockerfile
├── docker-compose.yml
│
├── scrape/                   # All scrapers
│   ├── casaevents.py
│   ├── eventbrit.py
│   ├── events.ma
│   └── guichet.py
│
├── struct_events/
│   └── models.py             # Events model

```

---



## ⚙️ Installation & Setup


### 1️⃣ Pull the Docker image
```bash
docker pull chaimaaeljerrar/scraping-image:latest
```


### 2️⃣ Create your .env file
```
ELASTIC_PASSWORD=(your elasic password)
CLOUD_ID=(your elastic cloud id)
```


### 3️⃣ Install dependencies
```
docker run -d -p 8000:8000 --env-file .env chaimaaeljerrar/scraping-image:latest
```


### 4️⃣ Access the frontend
```
👉 http://localhost:8000
🔌 Elasticsearch Connection
```



### 🤖 GitHub Actions – Scheduled Scraping
This automatically indexes new events every 10mins.



### 🖥️ Frontend – Usage
The frontend fetches events
Pagination is fully managed on the client side.



### 🔧 API Endpoints
| Method | Endpoint                | Description                       |
|--------|--------------------------|-----------------------------------|
| GET    | `/`                      | Frontend homepage                 |
| GET    | `/events?page=X&size=Y`  | Paginated events                  |
| GET    | `/indexing`              | Manually trigger event indexing   |
| GET    | `/stream`                | Server-sent events (debug)        |




### 🧪 Testing locally
```
Run FastAPI
Call: http://localhost:8000/events
If you see JSON, everything works.
Use the frontend to browse events visually.
```




### 📝 Future Improvements
```
1️⃣ Add categories & filters
2️⃣ Add search by city / date
3️⃣ Add infinite scrolling
4️⃣ Add AI-based event deduplication
```