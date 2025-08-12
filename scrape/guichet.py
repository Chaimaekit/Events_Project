import requests
from struct_events.models import Events
from into_db.connection import insert_events

def get_guichet():
    results = []
    try:
        url = "https://apiv2.guichet.com/v1/ticketing/events?limit=20&page=1"
        link = "https://guichet.com/ma-en/event/"

        while url:
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Request failed with status {response.status_code}")
                break

            try:
                data = response.json()
            except ValueError:
                print("Response is not valid JSON")
                break

            for event in data.get("events", []):
                send_event = Events(
                    id=str(event.get("id", "")),
                    name=event.get("title", ""),
                    description=event.get("meta", {}).get("description", ""),
                    date={
                        "customDate": event.get("customDate", ""),
                        "startAt": event.get("startAt", ""),
                        "endAt": event.get("closingTime", ""),
                    },
                    city=event.get("city", {}).get("name", ""),
                    place=event.get("place", {}).get("name", ""),
                    producer=event.get("producer", {}).get("title", ""),
                    category=[event.get("category", {}).get("title", "")],
                    offers=event.get("offers", []),
                    url=link + event.get("slug", "")
                ).model_dump()
                results.append(send_event)

            next_page = data.get("pagination", {}).get("nextPage")
            if next_page:
                url = f"https://apiv2.guichet.com/v1/ticketing/events?limit=20&page={next_page}"
            else:
                url = None
        return results

    except Exception as e:
        print(f"Error fetching Guichet events: {e}")
        return results
