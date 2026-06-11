from django.contrib import admin
from .models import ActivoFijo


@admin.register(ActivoFijo)
class ActivoFijoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'marca', 'numero_serie', 'estado', 'tecnico_asignado', 'valor']
    list_filter = ['estado']
    search_fields = ['nombre', 'numero_serie', 'tecnico_asignado']
