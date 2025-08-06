from pydantic import BaseModel, model_validator
from typing import Optional
from dateutil import parser


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
                parsed = parser.parse(date_str, dayfirst=True, fuzzy=True)
                return parsed.isoformat()
            except Exception:
                return None

        return {
            "customDate": parse_date(values.get("customDate")), 
            "startAt": parse_date(values.get("startAt")),
            "endAt": parse_date(values.get("endAt"))
        }
    
class Events(BaseModel):
    id: Optional[str]
    name: Optional[str]
    description: Optional[str]
    date: Optional[EventDate]
    city: Optional[str]
    place: Optional[str]
    producer: Optional[str]
    category: Optional[list[str]]
    offers: Optional[list[dict]]
    url: str

