from django.contrib import admin
from .models import Producto, MovimientoStock, OrdenCompra


class MovimientoStockInline(admin.TabularInline):
    model = MovimientoStock
    extra = 0
    readonly_fields = ['created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'sku', 'stock_actual', 'stock_minimo', 'stock_bajo', 'precio_venta']
    list_filter = ['stock_actual']
    search_fields = ['nombre', 'sku']
    inlines = [MovimientoStockInline]


@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    list_display = ['producto', 'tipo', 'cantidad', 'referencia', 'created_at']
    list_filter = ['tipo']


@admin.register(OrdenCompra)
class OrdenCompraAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'proveedor', 'fecha', 'fecha_limite_pago', 'estado', 'total']
    list_filter = ['estado']
