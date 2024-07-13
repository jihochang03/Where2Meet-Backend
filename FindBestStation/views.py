from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.response import Response
from .models import Station
from .utils import get_coordinates, calculate_midpoint, find_nearest_stations_kakao, find_best_station, transcoord_coordinates
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
    operation_description="Find the optimal subway station based on provided addresses",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'addresses': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
                description='List of addresses'
            ),
        },
        required=['addresses'],
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
        400: 'Invalid addresses or unable to find coordinates',
        404: 'No optimal station found',
    }
)
@api_view(['POST'])
def find_optimal_station(request):
    addresses = request.data.get('addresses', [])

    if not addresses or len(addresses) < 2 or len(addresses) > 5:
        return JsonResponse({'error': '2 to 5 addresses must be provided.'}, status=400)

    # Step 1: Get coordinates for each address
    locations = []
    for address in addresses:
        coordinates = get_coordinates(address)
        if coordinates:
            locations.append(coordinates)
        else:
            return JsonResponse({'error': f'Coordinates not found for address: {address}'}, status=404)

    # Step 2: Transform coordinates to desired coordinate system (example: WGS84 to KTM)
    transformed_locations = []
    for loc in locations:
        transformed_x, transformed_y = transcoord_coordinates(loc[1], loc[0], "WGS84", "KTM")
        if transformed_x is not None and transformed_y is not None:
            transformed_locations.append((transformed_x, transformed_y))
            print(f"x:{transformed_x}, y:{transformed_y}")
        else:
            return JsonResponse({'error': f'Failed to transform coordinates for location: {loc}'}, status=500)

    # Step 3: Calculate the midpoint of transformed coordinates
    midpoint = calculate_midpoint(transformed_locations)

    # Step 4: Find nearest subway stations to the midpoint
    nearest_stations = find_nearest_stations_kakao(midpoint)

    if not nearest_stations:
        return JsonResponse({'error': 'No nearby stations found.'}, status=404)
    
    best_station = find_best_station(nearest_stations)
    
    if best_station:
        return Response({
            "station_name": best_station.station_name,
            "coordinates": {"x": best_station.x, "y": best_station.y},
        })
    else:
        return Response({"error": "No optimal station found"}, status=404)
