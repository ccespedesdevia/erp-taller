from django.urls import path
from .views_api import identificar_equipo

urlpatterns = [
    path('identificar/', identificar_equipo, name='identificar_equipo'),
]
