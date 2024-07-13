from django.urls import path
from .views import find_optimal_station

urlpatterns = [
    path('find_optimal_station/', find_optimal_station, name='find_optimal_station'),
]
