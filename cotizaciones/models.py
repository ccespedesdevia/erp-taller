from django.db import models
from clientes.models import Cliente
from ordenes.models import OrdenServicio


class Cotizacion(models.Model):
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'), ('enviada', 'Enviada'),
        ('aprobada', 'Aprobada'), ('rechazada', 'Rechazada'),
    ]
    orden = models.ForeignKey(OrdenServicio, on_delete=models.SET_NULL, null=True, blank=True, related_name='cotizaciones', verbose_name='Orden de Servicio')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='cotizaciones', verbose_name='Cliente')
    fecha = models.DateField('Fecha', auto_now_add=True)
    valida_hasta = models.DateField('Válida hasta', null=True, blank=True)
    fecha_limite_pago = models.DateField('Fecha límite de pago', null=True, blank=True)
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='borrador')
    notas = models.TextField('Notas', blank=True)
    archivo_oc_cliente = models.FileField('OC del cliente', upload_to='ocs_cliente/', blank=True, help_text='Orden de compra que entrega el cliente')
    total = models.DecimalField('Total', max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)

    class Meta:
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'
        ordering = ['-fecha']

    def __str__(self):
        return f'COT #{self.id} - {self.cliente.razon_social}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        total = self.items.aggregate(
            total=models.Sum(models.F('cantidad') * models.F('precio_unitario'))
        )['total'] or 0
        if self.total != total:
            Cotizacion.objects.filter(pk=self.pk).update(total=total)


class ItemCotizacion(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items', verbose_name='Cotización')
    descripcion = models.CharField('Descripción', max_length=300)
    cantidad = models.IntegerField('Cantidad', default=1)
    precio_unitario = models.DecimalField('Precio unitario', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Item de cotización'
        verbose_name_plural = 'Items de cotización'

    def __str__(self):
        return f'{self.cantidad}x {self.descripcion}'

    def subtotal(self):
        return self.cantidad * self.precio_unitario
