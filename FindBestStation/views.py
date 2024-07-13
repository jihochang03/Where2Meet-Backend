from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.response import Response

from .utils import calculate_midpoint, find_nearest_stations_kakao, find_best_station, transcoord_coordinates, get_places
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
                        'x': openapi.Schema(type=openapi.TYPE_NUMBER, description='Longitude'),
                        'y': openapi.Schema(type=openapi.TYPE_NUMBER, description='Latitude'),
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
                        'x': openapi.Schema(type=openapi.TYPE_NUMBER, description='Longitude'),
                        'y': openapi.Schema(type=openapi.TYPE_NUMBER, description='Latitude'),
                    },
                ),
            }
        ),
        400: 'Invalid coordinates or unable to process',
        404: 'No optimal station found',
    }
)
@api_view(['POST'])
def find_optimal_station(request):
    locations = request.data.get('locations', [])
    factors = request.data.get('factors', [])

    if not locations or len(locations) < 2 or len(locations) > 5:
        return JsonResponse({'error': '2 to 5 locations must be provided.'}, status=400)

    if len(factors) > 6:
        return JsonResponse({'error': 'Up to 6 factors can be provided.'}, status=400)

    # Step 1: 입력받은 x,y를 구면좌표에서 평면좌표로 바꾸기(평균내기 위해서)
    transformed_locations = []
    for loc in locations:
        transformed_y, transformed_x = transcoord_coordinates(loc['x'], loc['y'], "WGS84", "KTM")
        if transformed_x is not None and transformed_y is not None:
            transformed_locations.append((transformed_x, transformed_y))
            print(f"x:{transformed_x}, y:{transformed_y}")
        else:
            return JsonResponse({'error': f'Failed to transform coordinates for location: {loc}'}, status=500)

    # Step 2: 바뀐 좌표를 평균내서 중간 지점을 잡고 중간 지점을 다시 구면좌표로 바꾸기
    midpoint = calculate_midpoint(transformed_locations)
    print(midpoint)

    # Step 3: 중간 지점에서 20km 반경의 지하철역 확인
    nearest_stations = find_nearest_stations_kakao(midpoint)
    if not nearest_stations:
        return JsonResponse({'error': 'No nearby stations found.'}, status=404)

    # Step 4: 최적의 장소를 팩터로 가중치 세워서 정리. 
    #여기가 아직 완성이 안됐어. 민서 오빠가 한 factor 1 적용하고 각각 팩터의 가중치 생각해야 될듯 지금은 1로 설정함. 
    best_station = find_best_station(nearest_stations, factors)

    if best_station:
        factors_query = '&'.join([f'factor={factor}' for factor in factors])
        redirect_url = f'/summary/?station_name={best_station["station_name"]}&{factors_query}'
        return Response({
            "station_name": best_station['station_name'],
            "coordinates": {"x": best_station['x'], "y": best_station['y']},
            "redirect_url": redirect_url
        })
    else:
        return Response({"error": "No optimal station found"}, status=404)

@swagger_auto_schema(
    method='get',
    operation_description="Search places based on keyword",
    manual_parameters=[
        openapi.Parameter('keyword', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Keyword to search for places')
    ],
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'place_name': openapi.Schema(type=openapi.TYPE_STRING, description='Place name'),
                    'address_name': openapi.Schema(type=openapi.TYPE_STRING, description='Address'),
                    'x': openapi.Schema(type=openapi.TYPE_NUMBER, description='Longitude'),
                    'y': openapi.Schema(type=openapi.TYPE_NUMBER, description='Latitude'),
                }
            )
        ),
        400: 'Invalid request or unable to process',
    }
)
@api_view(['GET'])
#키워드에 맞게 장소 검색해주는 거. 
def search_places(request):
    keyword = request.GET.get('keyword')
    if not keyword:
        return JsonResponse({'error': 'Keyword must be provided.'}, status=400)
    
    places = get_places(keyword)
    return JsonResponse(places, safe=False)
