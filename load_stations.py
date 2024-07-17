import os
import json
import django

# Django 프로젝트 설정 경로 지정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WhereShallWeMeet.settings')
django.setup()

from FindBestStation.models import Station

def load_stations_from_json(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            fields = item['fields']
            Station.objects.create(
                station_code=fields['station_code'],
                station_name=fields['station_name'],
                x=fields['x'],
                y=fields['y'],
                factor_2=fields['factor_2'],
                factor_3=fields['factor_3'],
                factor_4=fields['factor_4'],
                factor_5=fields['factor_5'],
                factor_6=fields['factor_6'],
                factor_7=fields['factor_7'],
            )

if __name__ == "__main__":
    load_stations_from_json('factor.json')
