import requests
from struct_events.models import Events
from into_db.connection import insert_events
import time

def get_guichet():
    results = []
    try:
        next_page = 1
        link = "https://guichet.com/ma-en/event/"
        

        while next_page is not None:
            url = "https://apiv2.guichet.com/v1/ticketing/events?limit=20&page=" + str(next_page)
            headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "dnt": "1",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "sec-ch-ua-platform": '"Windows"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua": '"Not.A/Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "accept-language": "en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1"
            }
            response = requests.get(url, headers=headers)
            time.sleep(5)
            if response.status_code != 200:
                print(f"Request failed with status {response.status_code}")
                break
            try:
                data = response.json()
            except ValueError:
                print("Response is not valid JSON")
                break
            try:
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
            except Exception as e:
                print(f"Error processing event data: {e}")
                return results
        return results

    except Exception as e:
        print(f"Error fetching Guichet events: {e}")
        return results
