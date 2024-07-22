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
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
OD_SAY_API_KEY = os.getenv("OD_SAY_API_KEY")
FORMAT = "json"
search_url = f"https://dapi.kakao.com/v2/local/search/keyword.{FORMAT}"
transcoord_url = f"https://dapi.kakao.com/v2/local/geo/transcoord.{FORMAT}"  # target URL


# EPSG:5179 좌표계 = 네이버 지도 좌표계
crs_epsg5179 = CRS.from_epsg(5179)
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
            region_1depth_name = documents[0].get('region_1depth_name', '')
            print(region_1depth_name)
            return (region_1depth_name)
            

def find_nearest_seoul(lon, lat):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {
        "query": "서울",
        "x": lon,
        "y": lat,
        "radius": 20000,  # 20km 내에서 검색
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
            raise ValueError("No Seoul location found within 20km radius.")
    else:
        raise ValueError("Error while searching for nearest Seoul location.")

def adjust_locations_to_seoul(locations):
    adjusted_locations = []
    
    for loc in locations:
        print(loc)
        lon, lat = loc['lon'], loc['lat']
        if is_within_seoul(lon, lat) == '서울특별시':
            adjusted_locations.append({'lon': lon, 'lat': lat})
        else:
            try:
                lon, lat = find_nearest_seoul(lon, lat)
                print(f"Adjusted location to Seoul: lon={lon}, lat={lat}")
                adjusted_locations.append({'lon': lon, 'lat': lat})
            except ValueError as e:
                print(e)
                return None  # If any location cannot be adjusted, return None
    return adjusted_locations

def calculate_midpoint(locations):
    adjusted_locations = adjust_locations_to_seoul(locations)
    if adjusted_locations is None:
        return 0, 0
    
    # WGS84 좌표를 EPSG:5179로 변환
    epsg5179_coords = [wgs84_to_epsg5179(loc['lon'], loc['lat']) for loc in adjusted_locations]
    
    # 중간점 계산
    midpoint_x = sum(coord[0] for coord in epsg5179_coords) / len(epsg5179_coords)
    midpoint_y = sum(coord[1] for coord in epsg5179_coords) / len(epsg5179_coords)

    # 중간점을 다시 WGS84로 변환
    midpoint_lat, midpoint_lon = epsg5179_to_wgs84(midpoint_y, midpoint_x)

    # # 최종 중간점이 서울 내에 있는지 확인하고, 아니면 가장 가까운 서울 내 위치로 이동
    # if not is_within_seoul(midpoint_lon, midpoint_lat):
    #     try:
    #         midpoint_lon, midpoint_lat = find_nearest_seoul(midpoint_lon, midpoint_lat)
    #         print(f"Adjusted midpoint to Seoul: lon={midpoint_lon}, lat={midpoint_lat}")
    #     except ValueError as e:
    #         print(e)
    #         return 0, 0

    return midpoint_lon, midpoint_lat


place_search_url = f"https://dapi.kakao.com/v2/local/search/keyword.{FORMAT}"

def find_nearest_stations_kakao(midpoint):
    headers = {
        "Authorization": f"KakaoAK {KAKAO_API_KEY}"
    }
    params = {
        "query": "지하철역",
        "x": midpoint[0],  # 경도
        "y": midpoint[1],  # 위도
        "radius": 20000,
        "sort": "distance",
    }
    
    response = requests.get(place_search_url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        stations = []
        added_station_names = set()  # 중복 역명을 체크하기 위한 집합
        for document in data['documents']:
            station_name_cleaned = document['place_name'].split(' ')[0]
            if station_name_cleaned not in added_station_names:
                station = {
                    'station_code': document['id'],
                    'station_name': station_name_cleaned,
                    'x': float(document['x']),
                    'y': float(document['y'])
                }
                stations.append(station)
                added_station_names.add(station_name_cleaned)
                # print(station)
        return stations
    else:
        print(f"Error in processing request: {response.status_code}")
        return []

def get_transit_time(start_x, start_y, end_x, end_y):
    base_url = "https://api.odsay.com/v1/api/searchPubTransPathT"
    params = {
        "SX": start_x,
        "SY": start_y,
        "EX": end_x,
        "EY": end_y,
        "apiKey": OD_SAY_API_KEY
    }
    encoded_params = urllib.parse.urlencode(params)
    request_url = f"{base_url}?{encoded_params}"
    
    try:
        response = requests.get(request_url)
        response.raise_for_status()  # Raise an error for bad status codes
        data = response.json()
        
        # 디버깅: API 응답 데이터 출력
        print(f"API Response: {data}")

        # Extract transit time from the response
        transit_time = None
        if 'result' in data and 'path' in data['result']:
            min_duration = float('inf')
            for path in data['result']['path']:
                duration = path['info']['totalTime']
                if duration < min_duration:
                    min_duration = duration
            transit_time = min_duration
        return transit_time

    except requests.exceptions.RequestException as e:
        print(f"Error fetching transit time: {e}")
        return None

def calculate_station_score(station, user_locations, factors, factor_weights):
    try:
        total_transit_time = 0

        # 멀티쓰레드로 각 사용자 위치에 대해 transit_time 요청
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(get_transit_time, user['lon'], user['lat'], station['x'], station['y']): user
                for user in user_locations
            }
            
            for future in as_completed(futures):
                try:
                    transit_time = future.result()
                    if transit_time is not None:
                        total_transit_time += transit_time
                    else:
                        total_transit_time += float('inf')  # If transit time cannot be fetched, assume it's very large
                except Exception as e:
                    print(f"Exception occurred: {e}")

        # 데이터베이스에서 station 정보 가져오기
        station_obj = Station.objects.get(station_name=station['station_name'])
        
        # Calculate the final score for the station
        final_score = 1.0
        for factor in factors:
            factor_attr = f'factor_{factor}'
            factor_value = getattr(station_obj, factor_attr, 0)
            final_score += factor_value * factor_weights[factor]
            
        if total_transit_time > 0:
            station_final_score = total_transit_time / final_score
        else:
            station_final_score = float('inf')

        return (station, station_final_score)

    except Station.DoesNotExist:
        print(f"Station with name {station['station_name']} does not exist.")
        return (station, float('inf'))
    except Exception as e:
        print(f"Error processing station {station['station_name']}: {e}")
        return (station, float('inf'))

def find_best_station(stations, user_locations, factors):
    factor_weights = {
        2: float(os.getenv('FACTOR_2_WEIGHT', 1)),
        3: float(os.getenv('FACTOR_3_WEIGHT', 1)),
        4: float(os.getenv('FACTOR_4_WEIGHT', 1)),
        5: float(os.getenv('FACTOR_5_WEIGHT', 1)),
        6: float(os.getenv('FACTOR_6_WEIGHT', 1)),
        7: float(os.getenv('FACTOR_7_WEIGHT', 1))
    }
    
    station_scores = []

    # 멀티쓰레드로 모든 역을 동시에 처리
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(calculate_station_score, station, user_locations, factors, factor_weights): station
            for station in stations
        }
        
        for future in as_completed(futures):
            try:
                station, score = future.result()
                print(f'station:{station}, score:{score}')
                station_scores.append((station, score))
            except Exception as e:
                print(f"Exception occurred: {e}")

    # 점수가 낮은 순서로 정렬하고 상위 3개 반환
    station_scores.sort(key=lambda x: x[1])
    return [station for station, score in station_scores[:3]]