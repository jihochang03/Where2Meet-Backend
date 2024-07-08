from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('query', openapi.IN_QUERY, description="Search keyword", type=openapi.TYPE_STRING),
    ],
    responses={200: openapi.Response('Success', openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)))}
)
@api_view(['GET'])
def search_places(request):
    query = request.GET.get('query', '')
    if not query:
        return JsonResponse({'error': 'No query provided'}, status=400)

    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {settings.KAKAO_API_KEY}"}
    params = {"query": query}
    
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    places = []

    if response.status_code == 200:
        for document in data.get('documents', []):
            place_info = {
                "name": document['place_name'],
                "address": document['road_address_name'],
                "latitude": document['y'],
                "longitude": document['x']
            }
            places.append(place_info)

    return JsonResponse(places, safe=False)

def calculate_average_location(locations):
    total_lat = 0
    total_lon = 0
    count = len(locations)
    for location in locations:
        total_lat += location['lat']
        total_lon += location['lon']
    average_lat = total_lat / count
    average_lon = total_lon / count
    return average_lat, average_lon

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'locations': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'lat': openapi.Schema(type=openapi.TYPE_NUMBER, description='Latitude'),
                        'lon': openapi.Schema(type=openapi.TYPE_NUMBER, description='Longitude')
                    }
                )
            )
        },
        required=['locations']
    ),
    responses={200: openapi.Response('Success', openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)))}
)
@api_view(['POST'])
def find_best_stations(request):
    data = json.loads(request.body)
    locations = data['locations']
    if not locations:
        return JsonResponse({'error': 'No locations provided'}, status=400)
    
    avg_lat, avg_lon = calculate_average_location(locations)
    
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {
        "query": "지하철역",
        "y": avg_lat,
        "x": avg_lon,
        "radius": 20000,  # 반경 20km 내에서 검색
        "sort": "distance"
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    stations = []

    if response.status_code == 200:
        for document in data.get('documents', [])[:10]:
            station_info = {
                "name": document['place_name'],
                "distance": document['distance'],
                "address": document['road_address_name'],
                "latitude": document['y'],
                "longitude": document['x']
            }
            stations.append(station_info)

    return JsonResponse(stations, safe=False)
