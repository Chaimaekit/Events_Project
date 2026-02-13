from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter


geolocator = Nominatim(user_agent="casablanca_events_app")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

def get_event_coords(address_text):
    full_address = f"{address_text}, Casablanca, Morocco"
    try:
        location = geocode(full_address)
        if location:
            return [location.longitude, location.latitude]
        else:
            return None
    except Exception as e:
        print(f"Error geocoding {address_text}: {e}")
        return None
