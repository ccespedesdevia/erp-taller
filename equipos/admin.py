from django.contrib import admin
from .models import Equipo


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'cliente', 'tipo', 'marca', 'numero_serie']
    list_filter = ['tipo']
    search_fields = ['marca', 'modelo', 'numero_serie', 'cliente__razon_social']
