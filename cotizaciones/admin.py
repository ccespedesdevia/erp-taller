from django.contrib import admin
from .models import Cotizacion, ItemCotizacion


class ItemCotizacionInline(admin.TabularInline):
    model = ItemCotizacion
    extra = 2


@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'estado', 'fecha', 'fecha_limite_pago', 'total']
    list_filter = ['estado']
    search_fields = ['cliente__razon_social']
    inlines = [ItemCotizacionInline]
    actions = ['marcar_enviada', 'marcar_aprobada']

    def marcar_enviada(self, request, queryset):
        queryset.update(estado='enviada')
    marcar_enviada.short_description = 'Marcar como enviada'

    def marcar_aprobada(self, request, queryset):
        queryset.update(estado='aprobada')
    marcar_aprobada.short_description = 'Marcar como aprobada'


admin.site.register(ItemCotizacion)
