# using heversine formula to calculate distance between long/lalt of event and bus/tramway in json
import math
import json
import networkx as nx
from scipy.spatial import cKDTree
import numpy as np

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
                    'name': nearest_bus.get('stations', []).get('name'),
                    'distance_km': bus_distance
                }
            if tramway_distance <= threshold_km:
                transport_info['nearest_tramway'] = {
                    'name': nearest_tramway.get('stations', []).get('name'),
                    'distance_km': tramway_distance
                }

            event['transport'] = transport_info

    return events

lignes_casabus = []
casabus_stops = []

def load_casabus_stops():
    with open('transport/tramway.json', 'r', encoding='utf-8') as f:
        stops_data = json.load(f)
        seen_names = set()
        for stop in stops_data.get("features", []):
            props = stop.get("properties", {})
            geom = stop.get("geometry", {})
            if geom.get("type") == "Point":
                coords = geom.get("coordinates", [])
                stop_name = props.get("name", "")
                if len(coords) == 2 and stop_name and stop_name not in seen_names:
                    casabus_stops.append({
                        "name": stop_name,
                        "ref": props.get("ref", ""),
                        "lon": coords[0],
                        "lat": coords[1]
                    })
                    seen_names.add(stop_name)
    print(f"Loaded {len(casabus_stops)} unique bus stops")


def calculate_casabus_lignes():
    cmp = 0
    with open('transport/lignes_tramway.json', 'r', encoding='utf-8') as f:
        casabus_lignes = json.load(f)
        for ligne in casabus_lignes.get("features", []):
            ligne_nb = ligne.get("properties", {}).get("ref", "")
            start = ligne.get("properties", {}).get("from", "")
            end = ligne.get("properties", {}).get("to", "")
            geom = ligne.get("geometry", {})
            coords = geom.get("coordinates", [])
            geom_type = geom.get("type", "")
            
            if geom_type == "LineString":
                flat_coords = coords
            elif geom_type == "MultiLineString":
                flat_coords = [point for line in coords for point in line]
            else:
                flat_coords = []
            
            if ligne_nb != "" and start != "" and end != "" and ligne_nb not in [l['ligne_nb'] for l in lignes_casabus]:
                lignes_casabus.append({
                    "ligne_nb": ligne_nb,
                    "start": start,
                    "end": end,
                    "coordinates": flat_coords,
                    "stations": []
                })
                cmp += 1
    print(f"Loaded {cmp} bus lines")

# def associate_stops_to_lines(threshold_km=0.1):
#     for ligne in lignes_casabus:
#         route_coords = ligne.get("coordinates", [])
#         for stop in casabus_stops:
#             stop_lon, stop_lat = stop["lon"], stop["lat"]
#             for route_point in route_coords:
#                 route_lon, route_lat = route_point
#                 distance = haversine(stop_lon, stop_lat, route_lon, route_lat)
#                 if distance <= threshold_km:
#                     if stop not in ligne["stations"]:
#                         ligne["stations"].append(stop)
#                     break

def stations_to_lines(threshold_km=0.1):
    stops_coords = np.array([[s['lon'], s['lat']] for s in casabus_stops])
    tree = cKDTree(stops_coords)
    
    for ligne in lignes_casabus:
        route_coords = ligne["coordinates"]
        associated_stops = set()
        for route_point in route_coords:
            route_lon, route_lat = route_point[:2]
            
            indices = tree.query_ball_point([route_lon, route_lat], 
                                           threshold_km / 111.0)
            
            for idx in indices:
                stop = casabus_stops[idx]
                dist = haversine(route_lon, route_lat, stop['lon'], stop['lat'])
                if dist <= threshold_km:
                    stop_id = stop['name']
                    if stop_id not in associated_stops:
                        ligne["stations"].append(stop)
                        associated_stops.add(stop_id)
        
        ligne['stations'] = sorted(
            ligne['stations'], 
            key=lambda s: int(s['ref'].split(';')[0]) if s['ref'] else 0
        )
        
        print(f"Ligne {ligne['ligne_nb']}: {len(ligne['stations'])} stations associated")

def build_bus_network():
    G = nx.Graph()
    
    for ligne in lignes_casabus:
        for i, station in enumerate(ligne['stations']):
            node_id = f"{station['name']}"
            G.add_node(node_id, 
                      name=station['name'],
                      ref=station['ref'],
                      lon=station['lon'],
                      lat=station['lat'])
            
            if i > 0:
                prev_station = ligne['stations'][i-1]
                prev_id = f"{prev_station['name']}"
                distance = haversine(station['lon'], station['lat'], 
                                    prev_station['lon'], prev_station['lat'])
                G.add_edge(prev_id, node_id, 
                          weight=distance, 
                          ligne=ligne['ligne_nb'])
    
    return G

load_casabus_stops()
calculate_casabus_lignes()
stations_to_lines()


bus_network = build_bus_network()

with open('transport/tram_lines_with_stations.json', 'w', encoding='utf-8') as f:
    json.dump(lignes_casabus, f, ensure_ascii=False, indent=4)

print("\n=== Bus Lines Summary ===")
for ligne in lignes_casabus:
    stations_list = [s['name'] for s in ligne['stations']]
    print(f"Ligne {ligne['ligne_nb']}: {ligne['start']} -> {ligne['end']}")
    print(f"  Stations ({len(ligne['stations'])}): {stations_list}")
    print()

print(f"Network Statistics:")
print(f"  Total Nodes: {bus_network.number_of_nodes()}")
print(f"  Total Edges: {bus_network.number_of_edges()}")

