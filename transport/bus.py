import math
import json
from scipy.spatial import KDTree
import numpy as np


def haversine(lon1, lat1, lon2, lat2):
    R = 6371
    dlon = math.radians(lon2 - lon1)
    dlat = math.radians(lat2 - lat1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    distance = R * c
    return distance


with open('transport/cleaned_lines/bus_lines_with_stations.json', 'r', encoding='utf-8') as f:
    lignes_casabus = json.load(f)

with open('transport/cleaned_lines/tram_lines_with_stations.json', 'r', encoding='utf-8') as f:
    lignes_tramway = json.load(f)


#Bus KDTree
bus_stop_coords = []
bus_stop_lines = []
for ligne in lignes_casabus:
    for point in ligne["coordinates"]:
        bus_stop_coords.append([point[0], point[1]])
        bus_stop_lines.append(ligne)
bus_tree = KDTree(np.array(bus_stop_coords))

#Tramway KDTree
tram_stop_coords = []
tram_stop_lines = []
for ligne in lignes_tramway:
    for point in ligne["coordinates"]:
        tram_stop_coords.append([point[0], point[1]])
        tram_stop_lines.append(ligne)
tram_tree = KDTree(np.array(tram_stop_coords))


def get_transport_info(event_coords, threshold_km=0.5):
    transport_info = {
        "bus_lines": [],
        "tramway_lines": []
    }

    if not event_coords or len(event_coords) < 2:
        return transport_info

    event_lon, event_lat = event_coords[0], event_coords[1]
    query_point = [event_lon, event_lat]
    radius = threshold_km / 111

    #bus
    seen = set()
    for i in bus_tree.query_ball_point(query_point, r=radius):
        ligne = bus_stop_lines[i]
        if ligne["ligne_nb"] not in seen:
            transport_info["bus_lines"].append({
                "ligne_nb": ligne["ligne_nb"],
                "start": ligne["start"],
                "end": ligne["end"]
            })
            seen.add(ligne["ligne_nb"])
            if len(transport_info["bus_lines"]) >= 3:
                break

    #tram
    seen = set()
    for i in tram_tree.query_ball_point(query_point, r=radius):
        ligne = tram_stop_lines[i]
        if ligne["ligne_nb"] not in seen:
            transport_info["tramway_lines"].append({
                "ligne_nb": ligne["ligne_nb"],
                "start": ligne["start"],
                "end": ligne["end"]
            })
            seen.add(ligne["ligne_nb"])
            if len(transport_info["tramway_lines"]) >= 3:
                break

    return transport_info