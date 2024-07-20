import requests
from math import radians, sin, cos, sqrt, atan2
from dotenv import load_dotenv
import os
from .models import Station
from pyproj import Transformer, CRS
import requests
import pandas as pd
from bs4 import BeautifulSoup
import urllib.parse

load_dotenv()
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
OD_SAY_API_KEY = os.getenv("OD_SAY_API_KEY")
FORMAT = "json"
search_url = f"https://dapi.kakao.com/v2/local/search/keyword.{FORMAT}"
transcoord_url = f"https://dapi.kakao.com/v2/local/geo/transcoord.{FORMAT}"  # target URL


# EPSG:5179 좌표계 = 네이버 지도 좌표계
crs_epsg5179 = CRS.from_epsg(3857)
# WGS84 좌표계 = 카카오맵 좌표계
crs_wgs84 = CRS.from_epsg(4326)

f_transformer = Transformer.from_crs(crs_epsg5179, crs_wgs84)
r_transformer = Transformer.from_crs(crs_wgs84, crs_epsg5179)

def wgs84_to_epsg5179(lon, lat):
  x, y = r_transformer.transform(lat, lon) # x, y
  return x, y

def epsg5179_to_wgs84(lon, lat):
  x, y = f_transformer.transform(lat, lon) # x, y
  return x, y

def is_within_seoul(lon, lat):
    url = "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"x": lon, "y": lat}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        documents = data.get('documents', [])
        if documents:
            region_2depth_name = documents[0].get('region_2depth_name', '')
            if '서울' in region_2depth_name:
                return True
    return False

def find_nearest_seoul(lon, lat):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {
        "query": "서울",
        "x": lon,
        "y": lat,
        "radius": 50000,  # 50km 내에서 검색
        "sort": "distance"
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        documents = data.get('documents', [])
        if documents:
            nearest_location = documents[0]
            nearest_lon = float(nearest_location['x'])
            nearest_lat = float(nearest_location['y'])
            return nearest_lon, nearest_lat
        else:
            raise ValueError("No Seoul location found within 50km radius.")
    else:
        raise ValueError("Error while searching for nearest Seoul location.")

def calculate_midpoint(locations):
    print(locations)

    # WGS84 좌표를 EPSG:5179로 변환
    epsg5179_coords = [wgs84_to_epsg5179(loc['lon'], loc['lat']) for loc in locations]

    # 중간점 계산
    midpoint_x = sum(coord[0] for coord in epsg5179_coords) / len(epsg5179_coords)
    midpoint_y = sum(coord[1] for coord in epsg5179_coords) / len(epsg5179_coords)
    print(f"midpoint_x: {midpoint_x}, midpoint_y: {midpoint_y}")

    # 중간점을 다시 WGS84로 변환
    midpoint_lon, midpoint_lat = epsg5179_to_wgs84(midpoint_x, midpoint_y)
    print(f"midpoint_lon: {midpoint_lon}, midpoint_lat: {midpoint_lat}")

    # 중간점이 서울 내에 있는지 확인하고, 아니면 가장 가까운 서울 내 위치로 이동
    if not is_within_seoul(midpoint_lon, midpoint_lat):
        try:
            midpoint_lon, midpoint_lat = find_nearest_seoul(midpoint_lon, midpoint_lat)
            print(f"Adjusted midpoint_lon: {midpoint_lon}, midpoint_lat: {midpoint_lat}")
        except ValueError as e:
            print(e)
            raise ValueError("Midpoint is not within 50km of Seoul and cannot be adjusted to a Seoul location.")

    return midpoint_lon, midpoint_lat


place_search_url = f"https://dapi.kakao.com/v2/local/search/keyword.{FORMAT}"

def find_nearest_stations_kakao(midpoint):
    headers = {
        "Authorization": f"KakaoAK {KAKAO_API_KEY}"
    }
    params = {
        "query": "지하철역",
        "x": midpoint[1],  # 경도
        "y": midpoint[0],  # 위도
        "radius": 5000,
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
            # 거리 필터링: 위도와 경도로부터 실제 거리를 계산하여 1000미터 이내의 역만 포함
            distance = calculate_distance(midpoint[0], midpoint[1], station['x'], station['y'])
            if distance <= 16000:
                stations.append(station)
                print(station)
        return stations
    else:
        print(f"Error in processing request: {response.status_code}")
        return []

def calculate_distance(lat1, lon1, lat2, lon2):
    from math import radians, cos, sin, sqrt, atan2
    
    R = 6371000  # 지구 반지름 (미터)
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) * sin(dlat / 2) + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) * sin(dlon / 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    print(distance)
    return distance

def get_transit_time(start_x, start_y, end_x, end_y):
    # ODsay API 호출 URL 생성
    print(start_x,start_y,end_x,end_y)
    base_url = "https://api.odsay.com/v1/api/searchPubTransPathT"
    params = {
        "SX": start_x,
        "SY": start_y,
        "EX": end_x,
        "EY": end_y,
        "apiKey": OD_SAY_API_KEY
    }
    encoded_params = urllib.parse.urlencode(params)
    # print(f"encodedparams={encoded_params}")
    request_url = f"{base_url}?{encoded_params}"
    print(request_url)
    
    try:
        response = requests.get(request_url)
        response.raise_for_status()  # Raise an error for bad status codes
        print(f"response={response}")
        # Assuming the API response is JSON
        data = response.json()

        # Extract transit time from the response
        transit_time = None
        if 'result' in data and 'path' in data['result']:
            # Find the journey with the minimum duration
            min_duration = float('inf')
            for path in data['result']['path']:
                duration = path['info']['totalTime']
                if duration < min_duration:
                    min_duration = duration
            transit_time = min_duration
        print(transit_time)
        return transit_time
    

    except requests.exceptions.RequestException as e:
        print(f"Error fetching transit time: {e}")
        return None

def find_best_station(stations, user_locations, factors):
    station_scores = []
    
    factor_2_weight= os.getenv('FACTOR_2_WEIGHT')
    factor_3_weight= os.getenv('FACTOR_3_WEIGHT')
    factor_4_weight= os.getenv('FACTOR_4_WEIGHT')
    factor_5_weight= os.getenv('FACTOR_5_WEIGHT')
    factor_6_weight= os.getenv('FACTOR_6_WEIGHT')
    factor_7_weight= os.getenv('FACTOR_7_WEIGHT')

    for station in stations:
        try:
            total_transit_time = 0
            for user_location in user_locations:
                transit_time = get_transit_time(user_location['lon'], user_location['lat'], station['x'], station['y'])
                print(f"transit_time={transit_time}")
                if transit_time:
                    total_transit_time += transit_time
                    print('yes_transit')
                else:
                    total_transit_time += float('inf')  # If transit time cannot be fetched, assume it's very large
                    print('no_transit')
            station_obj = Station.objects.get(station_name=station['station_name'])

            final_score = 1.0
            for factor in factors:
                factor_attr = f'factor_{factor}'
                factor_value = getattr(station_obj, factor_attr, 0)
            
                if factor == 2:
                    final_score += factor_value * factor_2_weight
                elif factor == 3:
                    final_score += factor_value * factor_3_weight
                elif factor == 4:
                    final_score += factor_value * factor_4_weight
                elif factor == 5:
                    final_score += factor_value * factor_5_weight
                elif factor == 6:
                    final_score += factor_value * factor_6_weight
                elif factor == 7:
                    final_score += factor_value * factor_7_weight
            # total_transit_time이 0인 경우를 처리하여 최종 점수 계산
            if total_transit_time > 0:
                final_score = 1 / final_score * total_transit_time
            else:
                final_score = float('inf')

            station_scores.append((station, final_score))

        except Station.DoesNotExist:
            print(f"Station with cleaned name {station['station_name']} does not exist.")
            continue

    # 점수가 낮은 순서로 정렬하고 상위 3개 반환
    station_scores.sort(key=lambda x: x[1])
    return [station for station, score in station_scores[:3]]