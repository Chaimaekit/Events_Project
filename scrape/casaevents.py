import requests
from bs4 import BeautifulSoup
from struct_events.models import Events
from into_db.connection import insert_events


def get_casa_events():
    try:
        response = requests.get("https://casaevents.ma/actualites/")
        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        items = soup.select_one("html > body > div:nth-of-type(3) > srcipt > div:nth-of-type(1) > div > div > div:nth-of-type(2) > div > div > div > div > div > div").find_all("div")
        for item in items:
            if len(item.find_all("div"))>1:
                link = item.find("a")['href']
                title = item.find_all("div")[0].text.strip()
                date = item.find_all("div")[1].text.strip()

                resp = requests.get(link)
                inside_soup = BeautifulSoup(resp.text, "html.parser")
                desc = inside_soup.select_one("div.post_ctn.clearfix div.entry")
                categ = inside_soup.select("div.post_ctn.clearfix div.post-info a")

                if title != "" and date !="":
                    send_event = Events(
                            id = "",
                            name = title,
                            description = desc.text.strip() if desc.text else "",
                            date = {
                                "customDate": "",
                                "startAt": date,
                                "endAt": "",
                            },
                            city = "Casablanca",
                            place = "",
                            producer = "Casablanca Events & Animation",
                            category = [name.text.strip() for name in categ if name.get("rel", []) == ['category', 'tag']],
                            offers = [],
                            url = link
                            ).model_dump()
                    results.append(send_event)
        return results
    except Exception as e:
        print("Error fetching Casa Events:", e)
        return results
    