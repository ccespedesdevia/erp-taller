from django.db import models, transaction
from django.db.models import Max
from clientes.models import Cliente
from inventario.models import Producto
from ordenes.models import OrdenServicio


class Configuracion(models.Model):
    nombre_empresa = models.CharField('Nombre empresa', max_length=200, default='CACD Soluciones')
    rut = models.CharField('RUT', max_length=20, default='')
    direccion = models.TextField('Dirección', blank=True)
    telefono = models.CharField('Teléfono', max_length=50, blank=True)
    email = models.EmailField('Email', blank=True)
    ultimo_numero_cotizacion = models.IntegerField('Último N° cotización', default=0)

    class Meta:
        verbose_name = 'Configuración'
        verbose_name_plural = 'Configuración'

    def __str__(self):
        return self.nombre_empresa

    @classmethod
    def obtener(cls):
        config, _ = cls.objects.get_or_create(pk=1, defaults={'nombre_empresa': 'CACD Soluciones'})
        return config


class Cotizacion(models.Model):
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'), ('enviada', 'Enviada'),
        ('aprobada', 'Aprobada'), ('rechazada', 'Rechazada'),
        ('anulada', 'Anulada'),
    ]
    numero = models.IntegerField('Número', unique=True, null=True, blank=True, editable=False)
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
        ordering = ['-numero']

    def __str__(self):
        return f'COT-{self.numero or self.id:05d} - {self.cliente.razon_social}'

    def save(self, *args, **kwargs):
        if not self.numero:
            with transaction.atomic():
                config = Configuracion.obtener()
                self.numero = (config.ultimo_numero_cotizacion or 0) + 1
                config.ultimo_numero_cotizacion = self.numero
                config.save()
        super().save(*args, **kwargs)
        if self.pk:
            total = sum(item.subtotal() for item in self.items.all())
            if self.total != total:
                Cotizacion.objects.filter(pk=self.pk).update(total=total)

    def total_neto(self):
        return sum(item.subtotal() for item in self.items.all())


class ItemCotizacion(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items', verbose_name='Cotización')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Producto')
    descripcion = models.CharField('Descripción', max_length=300)
    cantidad = models.IntegerField('Cantidad', default=1)
    precio_unitario = models.DecimalField('Precio unitario', max_digits=10, decimal_places=2)
    descuento = models.IntegerField('Descuento %', default=0)

    class Meta:
        verbose_name = 'Item de cotización'
        verbose_name_plural = 'Items de cotización'

    def __str__(self):
        return f'{self.cantidad}x {self.descripcion}'

    def subtotal(self):
        total = self.cantidad * self.precio_unitario
        if self.descuento:
            total = total * (1 - self.descuento / 100)
        return total


class CotizacionConsulta(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='consultas', verbose_name='Cotización')
    nombre = models.CharField('Nombre', max_length=200)
    email = models.EmailField('Email', blank=True)
    telefono = models.CharField('Teléfono', max_length=50, blank=True)
    mensaje = models.TextField('Mensaje')
    leido = models.BooleanField('Leído', default=False)
    created_at = models.DateTimeField('Creado', auto_now_add=True)

    class Meta:
        verbose_name = 'Consulta de cliente'
        verbose_name_plural = 'Consultas de clientes'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.nombre} - {self.cotizacion}'
