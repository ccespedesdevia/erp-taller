from django.db import models


class Producto(models.Model):
    sku = models.CharField('SKU', max_length=50, unique=True)
    nombre = models.CharField('Nombre', max_length=200)
    descripcion = models.TextField('Descripción', blank=True)
    precio_compra = models.DecimalField('Precio compra', max_digits=10, decimal_places=2, default=0)
    precio_venta = models.DecimalField('Precio venta', max_digits=10, decimal_places=2, default=0)
    stock_actual = models.IntegerField('Stock actual', default=0)
    stock_minimo = models.IntegerField('Stock mínimo', default=0, help_text='Alerta al llegar a este nivel')
    created_at = models.DateTimeField('Creado', auto_now_add=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} (SKU: {self.sku})'

    def stock_bajo(self):
        return self.stock_actual <= self.stock_minimo
    stock_bajo.boolean = True
    stock_bajo.short_description = 'Stock bajo'


class MovimientoStock(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'), ('salida', 'Salida'), ('ajuste', 'Ajuste'),
    ]
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='movimientos', verbose_name='Producto')
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES)
    cantidad = models.IntegerField('Cantidad')
    referencia = models.CharField('Referencia', max_length=200, blank=True, help_text='OC, orden de servicio, etc.')
    created_at = models.DateTimeField('Creado', auto_now_add=True)

    class Meta:
        verbose_name = 'Movimiento de Stock'
        verbose_name_plural = 'Movimientos de Stock'
        ordering = ['-created_at']


class OrdenCompra(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'), ('enviada', 'Enviada'),
        ('recibida', 'Recibida'), ('cancelada', 'Cancelada'),
    ]
    proveedor = models.CharField('Proveedor', max_length=200)
    fecha = models.DateField('Fecha', auto_now_add=True)
    fecha_limite_pago = models.DateField('Fecha límite de pago', null=True, blank=True)
    archivo = models.FileField('Archivo OC', upload_to='ocs/', blank=True, help_text='PDF o imagen de la OC del proveedor')
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    notas = models.TextField('Notas', blank=True)
    total = models.DecimalField('Total', max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField('Creado', auto_now_add=True)

    class Meta:
        verbose_name = 'Orden de Compra'
        verbose_name_plural = 'Órdenes de Compra'
        ordering = ['-fecha']

    def __str__(self):
        return f'OC #{self.id} - {self.proveedor} ({self.get_estado_display()})'
