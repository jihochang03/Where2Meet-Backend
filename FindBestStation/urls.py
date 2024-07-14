from django.urls import path
from .views import find_optimal_station #, search_places


urlpatterns = [
    path('find_optimal_station/', find_optimal_station, name='find_optimal_station'),
    #path('search_places/', search_places, name='search_places'),
]
