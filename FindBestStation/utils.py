import requests
from math import radians, sin, cos, sqrt, atan2
from dotenv import load_dotenv
import os
from .models import Station

load_dotenv()
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")

FORMAT = "json"
search_url = f"https://dapi.kakao.com/v2/local/search/keyword.{FORMAT}"
transcoord_url = f"https://dapi.kakao.com/v2/local/geo/transcoord.{FORMAT}" # target URL

def transcoord_coordinates(x, y, input_coord, output_coord):
    headers = {
        "Authorization": f"KakaoAK {KAKAO_API_KEY}"
    }
    params = {
        "x": x,
        "y": y,
        "input_coord": input_coord,
        "output_coord": output_coord
    }
    response = requests.get(transcoord_url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['documents']:
            return (float(data['documents'][0]['y']), float(data['documents'][0]['x']))  # Latitude, Longitude 순서로 반환
    print(f"Error or no results for coordinates transformation: {x}, {y}")
    return None

def calculate_midpoint(locations):
    x_coords = [loc[0] for loc in locations]
    y_coords = [loc[1] for loc in locations]
    midpoint_x = sum(x_coords) / len(x_coords)
    midpoint_y = sum(y_coords) / len(y_coords)
    print(f"midpoint_x: {midpoint_x}, midpoint_y:{midpoint_y}")
    return transcoord_coordinates(midpoint_x, midpoint_y, "KTM", "WGS84")

place_search_url = f"https://dapi.kakao.com/v2/local/search/keyword.{FORMAT}"

def find_nearest_stations_kakao(midpoint):
    headers = {
        "Authorization": f"KakaoAK {KAKAO_API_KEY}"
    }
    params = {
        "query": "지하철역",
        "x": midpoint[1],
        "y": midpoint[0],
        "radius": 20000,
        "size": 15,
        "sort": "distance",
        "category_group_code": "SW8",
    }
    response = requests.get(place_search_url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        stations = []
        for document in data['documents']:
            station_name_cleaned = document['place_name'].split(' ')[0]
            station = {
                'station_code': document['id'],
                'station_name': station_name_cleaned,
                'x': float(document['x']),
                'y': float(document['y'])
            }
            stations.append(station)
            print(station)
        return stations
    else:
        print(f"Error in processing request: {response.status_code}")
        return []

def find_best_station(stations, factors):
    best_station = None
    best_score = float('inf')

    for station in stations:
        try:
            print(f"Checking station with cleaned name: {station['station_name']}")
            station_obj = Station.objects.get(station_name=station['station_name'])
            score = sum(getattr(station_obj, f'factor_{i}') for i in factors)
            if score < best_score:
                best_score = score
                best_station = station
        except Station.DoesNotExist:
            print(f"Station with cleaned name {station['station_name']} does not exist.")
            continue

    return best_station

def get_places(keyword):
    headers = {
        "Authorization": f"KakaoAK {KAKAO_API_KEY}"
    }
    params = {
        "query": keyword,
        "page": 1,
        "size": 5,
        "sort": "accuracy"
    }
    response = requests.get(search_url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        places = []
        for document in data['documents']:
            place = {
                'place_name': document['place_name'],
                'address_name': document['address_name'],
                'x': float(document['x']),
                'y': float(document['y'])
            }
            places.append(place)
        return places
    else:
        print(f"Error or no results for query: {keyword}")
        return []