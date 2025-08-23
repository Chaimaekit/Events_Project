import requests
import time
from struct_events.models import Events
from into_db.connection import insert_events


def get_event_brit():

    results = []
    session = requests.Session()
    try:
        session.get("https://www.eventbrite.com/d/morocco/free--events/")

        csrf_token = session.cookies.get("csrftoken")
        headers = {
            "Referer": "https://www.eventbrite.com/d/morocco/free--events/",
            "x-csrftoken": csrf_token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }

        post_url = "https://www.eventbrite.com/api/v3/destination/search/"
        payload_base = {
                "browse_surface": "search",
                "event_search": {
                    "places": ["85632693"],
                    "online_events_only": False, 
                    "dates": ["current_future"], 
                    "sort": "quality",
                    "aggs": {
                        "organizertagsautocomplete_agg": {"size": 50}, 
                        "tags": {}, "dates": {}}           
                },
                "continuation": "eyJwYWdlIjogMn0",
                "expand.destination_event": []
            }
        post_response = session.post(post_url, headers=headers, json=payload_base)
        data = post_response.json()

        cmp = 0
        event_ids = ""

        for item in data.get("events", {}).get("results", []):
            cmp+= 1
            event_ids += "," + item.get("eventbrite_event_id")
            time.sleep(2)

        resp = requests.get(f"https://www.eventbrite.com/api/v3/destination/events/?event_ids={event_ids}&page_size={cmp}&expand=event_sales_status,image,primary_venue,saves,ticket_availability,primary_organizer,public_collections")
        data = resp.json()

        for obj in data.get("events", []):
            send_event = Events(
                id = obj.get("id", ""),
                name = obj.get("name", ""),
                description = obj.get("summary", ""),
                date = {
                        "customDate": obj.get("published", ""),
                        "startAt": obj.get("start_date", "") + obj.get("start_time", ""),
                        "endAt": obj.get("end_date", "") + obj.get("end_time", ""),
                        },
                city = obj.get("primary_venue", {}).get("address", {}).get("city", ""),
                place = obj.get("primary_venue", {}).get("address", {}).get("address_1", ""),
                producer = obj.get("primary_organizer", {}).get("name", ""),
                category = [categ.get("display_name", "") for categ in obj.get("tags", [])],
                offers = [obj.get("ticket_availability", {}).get("maximum_ticket_price", {}),obj.get("ticket_availability", {}).get("minimum_ticket_price", {})],
                url = obj.get("url", "")
                ).model_dump()
            results.append(send_event)
        return results
    except Exception as e:
        print(f"Error fetching Eventbrite events: {e}")
        return results
