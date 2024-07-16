from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.response import Response

from .utils import calculate_midpoint, find_nearest_stations_kakao, find_best_station
import requests
import os
from dotenv import load_dotenv

load_dotenv()
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")
FORMAT = "json"
search_url = f"https://dapi.kakao.com/v2/local/search/keyword.{FORMAT}"
transcoord_url = f"https://dapi.kakao.com/v2/local/geo/transcoord.{FORMAT}"

@swagger_auto_schema(
    method='post',
    operation_description="좌표와 팩터를 입력받아 최적의 장소를 찾기",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'locations': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'lon': openapi.Schema(type=openapi.TYPE_NUMBER, description='Longitude'),
                        'lat': openapi.Schema(type=openapi.TYPE_NUMBER, description='Latitude'),
                    }
                ),
                description='List of coordinates'
            ),
            'factors': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_INTEGER),
                description='List of factors to consider for scoring'
            ),
        },
        required=['locations'],
    ),
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'station_name': openapi.Schema(type=openapi.TYPE_STRING, description='Optimal station name'),
                'coordinates': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'lon': openapi.Schema(type=openapi.TYPE_NUMBER, description='Longitude'),
                        'lat': openapi.Schema(type=openapi.TYPE_NUMBER, description='Latitude'),
                    },
                ),
            }
        ),
        400: 'Invalid coordinates or unable to process',
        404: 'No optimal station found',
    }
)
@api_view(['POST', 'GET'])
def find_optimal_station(request):
    if request.method == 'POST':
        locations = request.data.get('locations', [])
        factors = request.data.get('factors', [])
    elif request.method == 'GET':
        locations = request.query_params.getlist('locations')
        factors = request.query_params.getlist('factors')
        # Convert locations and factors to appropriate types
        try:
            locations = [tuple(map(float, loc.split(','))) for loc in locations]
            locations = [{'lon': lon, 'lat': lat} for lon, lat in locations]
            factors = [int(factor) for factor in factors]
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    print(f"locations: {locations}")
    print(f"factors: {factors}")

    if not locations or len(locations) < 2 or len(locations) > 5:
        return JsonResponse({'error': '2 to 5 locations must be provided.'}, status=400)

    if len(factors) > 6:
        return JsonResponse({'error': 'Up to 6 factors can be provided.'}, status=400)

    midpoint = calculate_midpoint(locations)
    print(midpoint)

    # Step 3: 중간 지점에서 20km 반경의 지하철역 확인
    nearest_stations = find_nearest_stations_kakao(midpoint)
    if not nearest_stations:
        return JsonResponse({'error': 'No nearby stations found.'}, status=404)

    # Step 4: 최적의 장소를 팩터로 가중치 세워서 정리. 
    print("--------------------------------")
    print(f"nearest_stations: {nearest_stations}")
    print(f"locations: {locations}")
    print(f"factors: {factors}")
    best_stations = find_best_station(nearest_stations, locations, factors)

    if best_stations:
        results = []
        for best_station in best_stations:
            factors_query = '&'.join([f'factor_{factor}' for factor in factors])
            redirect_url = f'/summary/?station_name={best_station["station_name"]}&{factors_query}'
            result = {
                "station_name": best_station['station_name'],
                "coordinates": {"lon": best_station['x'], "lat": best_station['y']},
                "redirect_url": redirect_url,
                "factors": factors
            }
            results.append(result)
            print(best_station['x'], best_station['y'])
        
        return Response({"best_stations": results})
    else:
        return Response({"error": "No optimal station found"}, status=404)
