from django.contrib import admin
from .models import OrdenServicio, RepuestoUsado, FotoOrden


class RepuestoUsadoInline(admin.TabularInline):
    model = RepuestoUsado
    extra = 1


class FotoOrdenInline(admin.TabularInline):
    model = FotoOrden
    extra = 1


@admin.register(OrdenServicio)
class OrdenServicioAdmin(admin.ModelAdmin):
    list_display = ['codigo_seguimiento', '__str__', 'estado', 'tecnico', 'fecha_ingreso', 'horas_trabajadas', 'garantia_fin']
    list_filter = ['estado', 'tecnico']
    search_fields = ['cliente__razon_social', 'equipo__numero_serie', 'tecnico']
    inlines = [RepuestoUsadoInline, FotoOrdenInline]
    fieldsets = (
        ('Cliente y Equipo', {'fields': ['cliente', 'equipo', 'tecnico']}),
        ('Fechas', {'fields': ['fecha_ingreso', 'fecha_inicio', 'fecha_termino', 'fecha_entrega']}),
        ('Trabajo', {'fields': ['diagnostico', 'trabajo_realizado', 'software_instalado']}),
        ('Horas y Garantía', {'fields': ['horas_trabajadas', 'estado', 'garantia_fin']}),
        ('Interno', {'fields': ['notas_internas']}),
    )
    readonly_fields = ['fecha_ingreso']


admin.site.register(RepuestoUsado)
admin.site.register(FotoOrden)
