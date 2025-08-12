import requests
from struct_events.models import Events
from into_db.connection import insert_events


def get_guichet():
    response = requests.get(f"https://apiv2.guichet.com/v1/ticketing/events?limit=20&page=1")
    data = response.json()
    results = []
    link = "https://guichet.com/ma-en/event/"

    if response.status_code == 200:
            try:
                while data.get("pagination", {}).get("nextPage") is not None:
                    for event in data.get("events", []):
                        send_event = Events(
                            id = str(event.get("id", "")),
                            name = event.get("title", ""),
                            description = event.get("meta", {}).get("description", ""),
                            date = {
                                "customDate": event.get("customDate", ""),
                                "startAt": event.get("startAt", ""),
                                "endAt": event.get("closingTime", ""),
                            },
                            city = event.get("city").get("name", "") if event.get("city", {}) else "",
                            place = event.get("place", {}).get("name") if event.get("place", {}) else "",
                            producer = event.get("producer", {}).get("title") if event.get("producer", {}) else "",
                            category = [event.get("category", {}).get("title") if event.get("category", {}) else ""],
                            offers = event.get("offers", []),
                            url = link + event.get("slug", "")
                        ).model_dump()
                        results.append(send_event)
                    next_page = data["pagination"]["nextPage"]
                    response = requests.get(f"https://apiv2.guichet.com/v1/ticketing/events?limit=20&page={next_page}")
                    data = response.json()
                return results
            except Exception as e:
                print(f"Error processing Guichet events: {e}")
                return results
    else:
        print(f"Failed to fetch events from Guichet: {response.status_code}")
        return results
            
print(get_guichet())