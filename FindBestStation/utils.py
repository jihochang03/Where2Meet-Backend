import requests
from math import radians, sin, cos, sqrt, atan2
from dotenv import load_dotenv
import os
from .models import Station
from pyproj import Transformer, CRS
import requests
import pandas as pd
from bs4 import BeautifulSoup

load_dotenv()
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

FORMAT = "json"
search_url = f"https://dapi.kakao.com/v2/local/search/keyword.{FORMAT}"
transcoord_url = f"https://dapi.kakao.com/v2/local/geo/transcoord.{FORMAT}"  # target URL


# EPSG:5179 좌표계 = 네이버 지도 좌표계
crs_epsg5179 = CRS.from_epsg(3857)
# WGS84 좌표계 = 카카오맵 좌표계
crs_wgs84 = CRS.from_epsg(4326)

f_transformer = Transformer.from_crs(crs_epsg5179, crs_wgs84)
r_transformer = Transformer.from_crs(crs_wgs84, crs_epsg5179)

def epsg5179_to_wgs84(x, y):
  lat, lon = f_transformer.transform(x, y) # 위도, 경도 리턴
  return lon, lat

def wgs84_to_epsg5179(lon, lat):
  x, y = r_transformer.transform(lat, lon) # x, y
  return x, y

def calculate_midpoint(locations):
    lon = [loc['lon'] for loc in locations]
    lat = [loc['lat'] for loc in locations]
    midpoint_lon = sum(lon) / len(lon)
    midpoint_lat = sum(lat) / len(lat)
    print(f"midpoint_lon: {midpoint_lon}, midpoint_lat: {midpoint_lat}")
    return midpoint_lon, midpoint_lat


place_search_url = f"https://dapi.kakao.com/v2/local/search/keyword.{FORMAT}"

def find_nearest_stations_kakao(midpoint):
    headers = {
        "Authorization": f"KakaoAK {KAKAO_API_KEY}"
    }
    params = {
        "query": "지하철역",
        "x": midpoint[1],
        "y": midpoint[0],
        "radius": 1000,
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
                'lon': float(document['x']),
                'lat': float(document['y'])
            }
            stations.append(station)
            print(station)
        return stations
    else:
        print(f"Error in processing request: {response.status_code}")
        return []

def get_transit_time(start_lon, start_lat, end_lon, end_lat):
    headers = {
        "X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET
    }
    
    params = {
        "start": f"{start_lon},{start_lat}",
        "goal": f"{end_lon},{end_lat}",
        "option": "trafast"
    }
    
    x_1, y_1 = wgs84_to_epsg5179(start_lon, start_lat)
    x_2, y_2 = wgs84_to_epsg5179(end_lon, end_lat)
    
    transit_url = f"https://map.naver.com/p/directions/{x_1},{y_1},1,PLACE_POI/{x_2},{y_2},0,SUBWAY_STATION/-/transit?c=17.74,0,0,0,dh"
    
    try:
        response = requests.get(transit_url, headers=headers, params=params)
        response.raise_for_status()  # Raise an error for bad status codes

        # Assuming the API response is JSON
        data = response.json()

        # Extract transit time from the response
        transit_time = None
        if 'journeys' in data and data['journeys']:
            # Find the journey with the minimum duration
            min_duration = float('inf')
            for journey in data['journeys']:
                duration = journey['duration']
                if duration < min_duration:
                    min_duration = duration
            transit_time = min_duration
        
        return transit_time

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except KeyError as e:
        print(f"Key error while parsing response: {e}")
        return None
    except IndexError as e:
        print(f"No journeys found in response: {e}")
        return None
def find_best_station(stations, user_locations, factors):
    best_station = None
    best_score = float('inf')

    for station in stations:
        try:
            total_transit_time = 0
            # for user_location in user_locations:
            #     # transit_time = get_transit_time(user_location['lon'], user_location['lat'], station['lon'], station['lat'])
                # if transit_time:
                #     total_transit_time += transit_time
                # else:
                #     total_transit_time += float('inf')  # If transit time cannot be fetched, assume it's very large

            station_obj = Station.objects.get(station_name=station['station_name'])
            score = total_transit_time
            factor_2_weight = 1.0
            factor_3_weight = 1.0
            factor_4_weight = 1.0
            factor_5_weight = 1.0
            factor_6_weight = 1.0
            factor_7_weight = 1.0

            # 각 factor에 대한 가중치를 추가
            for factor in factors:
                factor_attr = f'factor_{factor}'
                factor_value = getattr(station_obj, factor_attr, 0)
                if factor == 2:
                    score += factor_value * factor_2_weight
                elif factor == 3:
                    score += factor_value * factor_3_weight
                elif factor == 4:
                    score += factor_value * factor_4_weight
                elif factor == 5:
                    score += factor_value * factor_5_weight
                elif factor == 6:
                    score += factor_value * factor_6_weight
                elif factor == 7:
                    score += factor_value * factor_7_weight

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
