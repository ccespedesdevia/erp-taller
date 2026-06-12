from django.urls import path
from .views_api import identificar_equipo, subir_informe

urlpatterns = [
    path('identificar/', identificar_equipo, name='identificar_equipo'),
    path('subir-informe/', subir_informe, name='subir_informe'),
]
