import json
import os
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter


geolocator = Nominatim(user_agent="evently_app_v1/1.0", timeout=10)
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.5)

COORDS_CACHE_FILE = os.path.join(os.path.dirname(__file__), "coords_cache.json")

def load_cache():
    if os.path.exists(COORDS_CACHE_FILE):
        with open(COORDS_CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(COORDS_CACHE_FILE, "w") as f:
        json.dump(cache, f)

coords_cache = load_cache()

def get_event_coords(address_text):
    if address_text in coords_cache:
        return coords_cache[address_text]

    attempts = [
        f"{address_text}, Casablanca, Morocco",
        f"{address_text} Casa, Morocco",
    ]

    for attempt in attempts:
        try:
            location = geocode(attempt)
            if location:
                result = [location.longitude, location.latitude]
                coords_cache[address_text] = result
                save_cache(coords_cache)
                return result
        except Exception as e:
            print(f"Error geocoding {attempt}: {e}")

    coords_cache[address_text] = None
    save_cache(coords_cache)
    return None