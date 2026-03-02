from pydantic import BaseModel, model_validator
from typing import Optional
from dateutil import parser
import pytz


class EventDate(BaseModel):
    customDate: Optional[str] = None
    startAt: Optional[str] = None
    endAt: Optional[str] = None

    @model_validator(mode="before")
    def normalize_dates(cls, values):
        def parse_date(date_str):
            if not date_str or not isinstance(date_str, str):
                return None
            try:
                tzinfos = {"CET": pytz.timezone("Africa/Casablanca")}
                parsed = parser.parse(date_str, dayfirst=True, fuzzy=True, tzinfos=tzinfos)
                return parsed.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                return None

        return {
            "customDate": parse_date(values.get("customDate")), 
            "startAt": parse_date(values.get("startAt")),
            "endAt": parse_date(values.get("endAt"))
        }
    
class Events(BaseModel):#rating
    id: Optional[str]
    name: Optional[str]
    img: Optional[str]
    description: Optional[str]
    date: Optional[EventDate]
    city: Optional[str]
    place: Optional[str]
    coordinates: Optional[list[float]]
    bus_lines: Optional[list[dict]]
    tramway_lines: Optional[list[dict]]
    producer: Optional[str]
    category: Optional[list[str]]
    offers: Optional[list[dict]]
    url: str

