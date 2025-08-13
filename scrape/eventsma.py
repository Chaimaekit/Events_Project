import requests
from struct_events.models import Events
from into_db.connection import insert_events


def get_event(data):
    link = "https://events.ma/concerts-festivals/"
    api_link = "https://bo.events.ma/api/event-details/"#+slug gives the event owner
    results = []
    for event in data:
            event_resp = requests.get(api_link+event.get("slug", ""))
            event_owner = event_resp.json().get("data", {})

            send_event = Events(
                id = str(event.get("id", "")),
                name = event.get("meta_title", ""),
                description = event.get("meta_description", ""),
                date = {
                    "customDate": event.get("customDate", ""),
                    "startAt": event.get("date_start", ""),
                    "endAt": event.get("date_end", ""),
                },
                city = event.get("scene", {}).get("city", {}).get("name", "") if event.get("scene", {}) else "",
                place = str(event.get("scene", {}).get("libelle", "")) +" "+ str(event.get("scene", {}).get("address", "")) if event.get("scene", {}) else "",
                producer = str(event_owner.get("event_owner", {}).get("first_name","")) + " " +str(event_owner.get("event_owner", {}).get("last_name","")),
                category = [event.get("categories")[0].get("labelle", "") if event.get("categories") else ""],
                offers = event.get("sieges", []),
                url = link + event.get("slug", "")
            ).model_dump()
            results.append(send_event)
    return results

def get_events_ma():

    results = []
    session = requests.Session()
    try:
        resp = session.post("https://bo.events.ma/api/events-by-category",json={"category": "", "limit": 10, "offset": 0})#while len(data) > 0 limit10 offset+=10
        data = resp.json().get("data", [])
        offset = 0
        
        while len(data) > 0:
            offset+=10
            for result in get_event(data):
                results.append(result)
            resp = session.post("https://bo.events.ma/api/events-by-category",json={"category": "", "limit": 10, "offset": offset})
            data = resp.json().get("data", [])
        return results
    except Exception as e:
        print(f"Error fetching Events.ma events: {e}")
        return results
