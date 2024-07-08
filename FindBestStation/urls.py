from django.urls import path
from .views import find_best_stations, search_places

urlpatterns = [
    path('find_best_stations/', find_best_stations, name='find_best_stations'),
    path('search_places/', search_places, name='search_places'),
]
