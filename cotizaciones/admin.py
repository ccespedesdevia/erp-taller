from django.contrib import admin
from django.utils.html import format_html
from .models import Cotizacion, ItemCotizacion, CotizacionConsulta, Configuracion


class ItemCotizacionInline(admin.TabularInline):
    model = ItemCotizacion
    extra = 2
    fields = ['producto', 'recurso', 'descripcion', 'cantidad', 'unidad', 'precio_unitario', 'descuento', 'porcentaje_descuento_item', 'total_item']
    readonly_fields = ['total_item']
    autocomplete_fields = ['producto']


class CotizacionConsultaInline(admin.TabularInline):
    model = CotizacionConsulta
    extra = 0
    readonly_fields = ['nombre', 'email', 'telefono', 'mensaje', 'created_at']
    can_delete = False
    verbose_name = 'Consulta de cliente'
    verbose_name_plural = 'Consultas de clientes'

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'cliente', 'fecha', 'valida_hasta', 'estado_coloreado', 'total_formateado', 'num_consultas', 'link_publico']
    list_filter = ['estado', 'fecha']
    search_fields = ['numero', 'cliente__razon_social']
    inlines = [ItemCotizacionInline, CotizacionConsultaInline]
    readonly_fields = ['numero', 'fecha', 'subtotal', 'monto_descuento', 'neto', 'iva', 'total', 'created_at', 'updated_at', 'link_publico']
    fieldsets = (
        ('Información general', {'fields': ['numero', 'cliente', 'orden', 'fecha', 'valida_hasta', 'estado']}),
        ('Negocio', {'fields': ['unidad_negocio', 'moneda', 'forma_pago', 'archivo_oc_cliente'], 'classes': ['collapse']}),
        ('Detalle', {'fields': ['notas', 'observaciones', 'incluye'], 'classes': ['collapse']}),
        ('Totales', {'fields': ['subtotal', 'porcentaje_descuento', 'monto_descuento', 'neto', 'iva', 'total']}),
        ('Documentos y previsualización', {'fields': ['link_publico']}),
    )
    actions = ['marcar_enviada', 'marcar_aprobada', 'duplicar_cotizacion', 'recalcular_totales']

    def codigo(self, obj):
        return f'COT-{obj.numero:05d}' if obj.numero else f'COT-#{obj.id}'
    codigo.short_description = 'Código'
    codigo.admin_order_field = 'numero'

    def estado_coloreado(self, obj):
        colores = {'borrador': 'secondary', 'enviada': 'info', 'aprobada': 'success', 'rechazada': 'danger', 'anulada': 'dark'}
        color = colores.get(obj.estado, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_estado_display())
    estado_coloreado.short_description = 'Estado'

    def total_formateado(self, obj):
        return format_html('${}', '{:,.0f}'.format(float(obj.total)))
    total_formateado.short_description = 'Total'

    def num_consultas(self, obj):
        count = obj.consultas.count()
        no_leidas = obj.consultas.filter(leido=False).count()
        if no_leidas:
            return format_html('{} <span class="badge bg-warning text-dark">{}</span>', count, no_leidas)
        return str(count)
    num_consultas.short_description = 'Consultas'

    def link_publico(self, obj):
        n = obj.numero or obj.id
        consultar_url = f'/cotizaciones/{n}/consultar/'
        pdf_url = f'/portal/cotizaciones/{n}/pdf/'
        return format_html(
            '<a href="{}" target="_blank">🔗 Pública</a> &nbsp;|&nbsp; '
            '<a href="{}" target="_blank">📄 PDF</a>',
            consultar_url, pdf_url
        )
    link_publico.short_description = 'Previsualizar'

    def marcar_enviada(self, request, queryset):
        queryset.update(estado='enviada')
    marcar_enviada.short_description = 'Marcar como enviada'

    def marcar_aprobada(self, request, queryset):
        queryset.update(estado='aprobada')
    marcar_aprobada.short_description = 'Marcar como aprobada'

    def duplicar_cotizacion(self, request, queryset):
        for original in queryset:
            items_data = list(original.items.values('producto_id', 'recurso', 'descripcion', 'cantidad', 'unidad', 'precio_unitario', 'descuento', 'porcentaje_descuento_item'))
            nueva = Cotizacion(
                cliente=original.cliente,
                valida_hasta=original.valida_hasta,
                notas=f'Duplicado de COT-{original.numero:05d}\n\n{original.notas}',
                unidad_negocio=original.unidad_negocio,
                moneda=original.moneda,
                forma_pago=original.forma_pago,
                porcentaje_descuento=original.porcentaje_descuento,
            )
            nueva.save()
            for item_data in items_data:
                ItemCotizacion.objects.create(cotizacion=nueva, **item_data)
            nueva.recalcular_totales()
    duplicar_cotizacion.short_description = 'Duplicar cotización seleccionada'

    def recalcular_totales(self, request, queryset):
        for cot in queryset:
            cot.recalcular_totales()
        self.message_user(request, f'{queryset.count()} cotización(es) recalculada(s).')
    recalcular_totales.short_description = 'Recalcular totales seleccionadas'


@admin.register(Configuracion)
class ConfiguracionAdmin(admin.ModelAdmin):
    list_display = ['nombre_empresa', 'rut', 'giro', 'ultimo_numero_cotizacion']
    fieldsets = (
        ('Empresa', {'fields': ['nombre_empresa', 'rut', 'giro', 'direccion', 'telefono', 'email', 'email_recepcion_dte']}),
        ('Numeración', {'fields': ['ultimo_numero_cotizacion']}),
        ('Términos legales', {'fields': ['terminos_legales'], 'classes': ['wide']}),
    )

    def has_add_permission(self, request):
        return not Configuracion.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CotizacionConsulta)
class CotizacionConsultaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'cotizacion', 'email', 'telefono', 'leido', 'created_at']
    list_filter = ['leido']
    search_fields = ['nombre', 'cotizacion__numero', 'mensaje']
    readonly_fields = ['nombre', 'email', 'telefono', 'mensaje', 'created_at']
    actions = ['marcar_leidas']

    def marcar_leidas(self, request, queryset):
        queryset.update(leido=True)
    marcar_leidas.short_description = 'Marcar como leídas'
