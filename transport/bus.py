# using heversine formula to calculate distance between long/lalt of event and bus/tramway in json
import math

def haversine(lon1, lat1, lon2, lat2):
    R = 6371
    dlon = math.radians(lon2 - lon1)
    dlat = math.radians(lat2 - lat1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    distance = R * c
    return distance

def nearest_transport(event_coords, transport_data):
    nearest_transport = None
    min_distance = float('inf')

    event_lat, event_lon = event_coords

    for transport in transport_data:
        transport_lat = transport.get('geometry', {}).get('coordinates', [])[1]
        transport_lon = transport.get('geometry', {}).get('coordinates', [])[0]

        distance = haversine(event_lon, event_lat, transport_lon, transport_lat)

        if distance < min_distance:
            min_distance = distance
            nearest_transport = transport

    return nearest_transport, min_distance

def events_with_transport(events, bus_data, tramway_data, threshold_km=1.0):
    for event in events:
        coords = event.get('coordinates')
        if coords:
            nearest_bus, bus_distance = nearest_transport(coords, bus_data)
            nearest_tramway, tramway_distance = nearest_transport(coords, tramway_data)

            transport_info = {}
            if bus_distance <= threshold_km:
                transport_info['nearest_bus'] = {
                    'name': nearest_bus.get('name'),
                    'distance_km': bus_distance
                }
            if tramway_distance <= threshold_km:
                transport_info['nearest_tramway'] = {
                    'name': nearest_tramway.get('name'),
                    'distance_km': tramway_distance
                }

            event['transport'] = transport_info

    return events