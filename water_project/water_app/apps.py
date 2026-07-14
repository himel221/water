# water_app/apps.py

from django.apps import AppConfig

class WaterAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'water_app'
    verbose_name = 'Water App'
    
    def ready(self):
     
        pass