import requests
from dotenv import load_dotenv
import os
from .models import Station
from pyproj import Transformer, CRS
import requests
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
FORMAT = "json"
search_url = f"https://dapi.kakao.com/v2/local/search/keyword.{FORMAT}"
transcoord_url = f"https://dapi.kakao.com/v2/local/geo/transcoord.{FORMAT}"  # target URL
api_keys = []
api_key_idx = 0

def load_api_keys():
    global api_keys
    idx = 1
    while True:
        key = os.getenv(f'ODSAY_API_KEY{idx}')
        if key is None:
            break
        api_keys.append(key)
        idx += 1
        
def get_next_api_key():
    global api_key_idx
    key = api_keys[api_key_idx]
    api_key_idx = (api_key_idx + 1) % N
    return key

load_api_keys()
N = len(api_keys)  # API 키의 총 개수

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

def adjust_location(loc):
    lon, lat = loc['lon'], loc['lat']
    if is_within_seoul(lon, lat) == '서울특별시':
        return {'lon': lon, 'lat': lat}
    else:
        try:
            lon, lat = find_nearest_seoul(lon, lat)
            print(f"Adjusted location to Seoul: lon={lon}, lat={lat}")
            return {'lon': lon, 'lat': lat}
        except ValueError as e:
            print(e)
            return None

def adjust_locations_to_seoul(locations):
    adjusted_locations = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_location = {executor.submit(adjust_location, loc): loc for loc in locations}
        for future in as_completed(future_to_location):
            result = future.result()
            if result:
                adjusted_locations.append(result)
            else:
                print(f"Failed to adjust location: {future_to_location[future]}")
                return None
    return adjusted_locations

def calculate_midpoint(locations):
    
    adjusted_locations = adjust_locations_to_seoul(locations)
    if adjusted_locations is None:
        return 0, 0
    
    epsg5179_coords = [wgs84_to_epsg5179(loc['lon'], loc['lat']) for loc in adjusted_locations]

    midpoint_x = sum(coord[0] for coord in epsg5179_coords) / len(epsg5179_coords)
    midpoint_y = sum(coord[1] for coord in epsg5179_coords) / len(epsg5179_coords)

    midpoint_lat, midpoint_lon = epsg5179_to_wgs84(midpoint_y, midpoint_x)
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
        added_station_names = set() 
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
        return stations
    else:
        print(f"Error in processing request: {response.status_code}")
        return []
    

def get_transit_time(start_x, start_y, end_x, end_y):
    base_url = "https://api.odsay.com/v1/api/searchPubTransPathT"
    api_key = get_next_api_key()
    params = {
        "SX": start_x,
        "SY": start_y,
        "EX": end_x,
        "EY": end_y,
        "apiKey": api_key
    }
    encoded_params = urllib.parse.urlencode(params)
    request_url = f"{base_url}?{encoded_params}"

    retries = 10
    delay = 0.3

    for attempt in range(retries):
        try:
            response = requests.get(request_url)
            response.raise_for_status()
            data = response.json()

            if 'result' in data and 'path' in data['result']:
                min_duration = float('inf')
                for path in data['result']['path']:
                    duration = path['info']['totalTime']
                    if duration < min_duration:
                        min_duration = duration
                return min_duration if min_duration != float('inf') else 120
            elif 'error' in data:
                # retry with a different api key
                api_key = get_next_api_key()
                time.sleep(0.3)
            else:
                raise requests.exceptions.RequestException("No result or error in response")
        except requests.exceptions.RequestException as e:
            return 120  # Return 120 minutes if request fails

    return 120

def find_best_station(stations, user_locations, factors):
    station_scores = []
    factor_weights = {
        2: float(os.getenv('FACTOR_2_WEIGHT', 1)),
        3: float(os.getenv('FACTOR_3_WEIGHT', 1)),
        4: float(os.getenv('FACTOR_4_WEIGHT', 1)),
        5: float(os.getenv('FACTOR_5_WEIGHT', 1)),
        6: float(os.getenv('FACTOR_6_WEIGHT', 1)),
        7: float(os.getenv('FACTOR_7_WEIGHT', 1))
    }
    
    def fetch_transit_time_for_station(station, user_location):
        return get_transit_time(user_location['lon'], user_location['lat'], station['x'], station['y'])
    
    def process_station(station):
        try:
            total_transit_time = 0
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {
                    executor.submit(fetch_transit_time_for_station, station, user): user
                    for user in user_locations
                }
                
                for future in as_completed(futures):
                    try:
                        transit_time = future.result()
                        if transit_time:
                            total_transit_time += transit_time
                        else:
                            total_transit_time += float('inf')
                    except Exception as e:
                        print(f"Exception occurred: {e}")

            station_obj = Station.objects.get(station_name=station['station_name'])
            
            final_score = 1.0
            for factor in factors:
                factor_attr = f'factor_{factor}'
                factor_value = getattr(station_obj, factor_attr, 0)
                final_score += factor_value * factor_weights[factor]
                

            print(f'station:{station}, final_score:{final_score}, total_transit_time:{total_transit_time}')
            return (station, final_score, total_transit_time)

        except Exception as e:
            print(f"Error processing station {station['station_name']}: {e}")
            return (station, float(0), float('inf'))

    try:
        with ThreadPoolExecutor(max_workers=10) as station_executor:
            station_futures = {station_executor.submit(process_station, station): station for station in stations}
            transit_times = []
            for future in as_completed(station_futures):
                station, station_score, transit_time = future.result()
                station_scores.append((station, station_score, transit_time))
                transit_times.append(transit_time)
        
        max_time = max(transit_times)
        min_time = min(transit_times)
        
        final_station_scores = [(station, station_score + (1-((transit_time - min_time)/(max_time-min_time))) * 2) for (station, station_score, transit_time) in station_scores]
        
        final_station_scores.sort(key=lambda x: x[1],reverse=True)
        return [station for station, score in final_station_scores[:3]]

    except Exception as e:
        print(f"Error processing stations: {e}")

# def find_best_station(stations, user_locations, factors):
#     station_scores = []
#     factor_weights = {
#         2: float(os.getenv('FACTOR_2_WEIGHT', 1)),
#         3: float(os.getenv('FACTOR_3_WEIGHT', 1)),
#         4: float(os.getenv('FACTOR_4_WEIGHT', 1)),
#         5: float(os.getenv('FACTOR_5_WEIGHT', 1)),
#         6: float(os.getenv('FACTOR_6_WEIGHT', 1)),
#         7: float(os.getenv('FACTOR_7_WEIGHT', 1))
#     }
#     total_transit_times = []

#     def fetch_total_transit_time(station):
#         total_transit_time = 0
#         with ThreadPoolExecutor(max_workers=len(user_locations)) as executor:
#             futures = {
#                 executor.submit(get_transit_time, user['lon'], user['lat'], station['x'], station['y']): user
#                 for user in user_locations
#             }
#             for future in as_completed(futures):
#                 try:
#                     transit_time = future.result()
#                     if transit_time is None:
#                         transit_time = float('inf')
#                     total_transit_time += transit_time
#                 except Exception as e:
#                     print(f"Exception occurred while fetching transit time: {e}")
#                     total_transit_time += float('inf')

#         total_transit_times.append(total_transit_time)
#         return total_transit_time

#     try:
#         with ThreadPoolExecutor(max_workers=len(stations)) as station_executor:
#             station_futures = {station_executor.submit(fetch_total_transit_time, station): station for station in stations}
#             results = []

#             for future in as_completed(station_futures):
#                 station = station_futures[future]
#                 total_transit_time = future.result()
#                 results.append((station, total_transit_time))

#         min_transit_time = min(total_transit_times)
#         max_transit_time = max(total_transit_times)
#         range_transit_time = (max_transit_time - min_transit_time) if max_transit_time > min_transit_time else 1

#         for station, total_transit_time in results:
#             normalized_transit_time = (total_transit_time - min_transit_time) / range_transit_time

#             try:
#                 station_obj = Station.objects.get(station_name=station['station_name'])
#             except Station.DoesNotExist:
#                 print(f"Station {station['station_name']} not found in the database.")
#                 continue

#             factor_score = normalized_transit_time

#             for factor in range(2, 8):
#                 factor_score += getattr(station_obj, f'factor_{factor}', 0)

#             for factor in factors:
#                 factor_score += getattr(station_obj, f'factor_{factor}', 0) * factor_weights[factor]

#             station_scores.append((station, factor_score))

#         station_scores.sort(key=lambda x: x[1], reverse=True)
#         return [station for station, score in station_scores[:3]]

#     except Exception as e:
#         print(f"Error processing stations: {e}")
#         return None