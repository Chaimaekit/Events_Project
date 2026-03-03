import requests
from bs4 import BeautifulSoup
from struct_events.models import Events
import traceback
from struct_events.get_coords import get_event_coords


def get_casa_events():
    try:
        response = requests.get("https://casaevents.ma/actualites/")
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        items = soup.select_one("html > body > div:nth-of-type(3) > srcipt > div:nth-of-type(1) > div > div > div:nth-of-type(2) > div > div > div > div > div > div")
        if not items:
            print("Warning: Could not find events container in casaevents.ma")
            return results
        
        items = items.find_all("div")
        for item in items:
            try:
                if len(item.find_all("div")) > 1:
                    link = item.find("a")['href']
                    title = item.find("a")['title']
                    img = item.find("img")['src'] if item.find("img") else ""
                    date = item.find_all("div")[1].find_all("div")[1].text.strip() if len(item.find_all("div")[1].find_all("div")) > 1 else None

                    resp = requests.get(link)
                    inside_soup = BeautifulSoup(resp.text, "html.parser")
                    desc = inside_soup.select_one("div.post_ctn.clearfix div.entry")
                    categ = inside_soup.select("div.post_ctn.clearfix div.post-info a")

                    if title != "" and date is not None:
                        send_event = Events(
                                id = "",
                                name = title,
                                img = img,
                                description = desc.text.strip() if desc and desc.text else "No description available",
                                date = {
                                    "customDate": None,
                                    "startAt": date,
                                    "endAt": None,
                                },
                                city = "Casablanca",
                                place = "Casablanca",
                                coordinates = get_event_coords("Casablanca"),
                                producer = "Casablanca Events & Animation",
                                category = [name.text.strip() for name in categ if name.get("rel", []) == ['category', 'tag']] or ["Event"],
                                offers = [],
                                url = link
                                ).model_dump()
                        results.append(send_event)
            except Exception as item_err:
                print(f"Error processing individual event from casaevents: {item_err}")
                continue
        return results
    except Exception as e:
        print("Error fetching Casa Events:", e)
        traceback.print_exc()
        return results