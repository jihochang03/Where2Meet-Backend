from django.db import models

class Station(models.Model):
    station_code = models.CharField(max_length=20, unique=True)
    station_name = models.CharField(max_length=100)
    x = models.FloatField()
    y = models.FloatField()
    factor_2 = models.FloatField()
    factor_3 = models.FloatField()
    factor_4 = models.FloatField()
    factor_5 = models.FloatField()
    factor_6 = models.FloatField()
    factor_7 = models.FloatField()

    def __str__(self):
        return self.station_name
