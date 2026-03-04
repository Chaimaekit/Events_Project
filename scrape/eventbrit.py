import requests
import time
from struct_events.models import Events
from struct_events.get_coords import get_event_coords



def concat_datetime(date, time):
    if date and time:
        return f"{date} {time}"
    return date or None

def get_event_brit():

    results = []
    session = requests.Session()
    try:#the block needs to request on the other pages 1,2,3... to get the rest of the events
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
            place = obj.get("primary_venue", {}).get("address", {}).get("address_1", "")
            city = obj.get("primary_venue", {}).get("address", {}).get("city", "")
            coords = None
            if city and "casablanca" in city.lower():
                coords = get_event_coords(place) if place else get_event_coords(city)
            
            send_event = Events(
                id = obj.get("id", ""),
                name = obj.get("name", ""),
                img = obj.get("image", {}).get("original", {}).get("url", ""),
                description = obj.get("summary", "") or "No description available",
                date = {
                        "customDate": obj.get("published", None),
                        "startAt": concat_datetime(obj.get("start_date", None), obj.get("start_time", None)),
                        "endAt": concat_datetime(obj.get("end_date", None), obj.get("end_time", None)),
                        },
                city = city or "Unknown",
                place = place or "Unknown",
                coordinates = coords,
                producer = obj.get("primary_organizer", {}).get("name", "") or "Unknown Producer",
                category = [categ.get("display_name", "") for categ in obj.get("tags", [])] or ["Event"],
                offers = [obj.get("ticket_availability", {}).get("maximum_ticket_price", {}),obj.get("ticket_availability", {}).get("minimum_ticket_price", {})],
                url = obj.get("url", "")
                ).model_dump()
            results.append(send_event)
        return results
    except Exception as e:
        print(f"Error fetching Eventbrite events: {e}")
        return results
