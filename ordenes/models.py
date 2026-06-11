import datetime
from django.db import models
from clientes.models import Cliente
from equipos.models import Equipo
from inventario.models import Producto


class OrdenServicio(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'), ('en_curso', 'En Curso'),
        ('completado', 'Completado'), ('facturado', 'Facturado'),
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='ordenes', verbose_name='Cliente')
    equipo = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordenes', verbose_name='Equipo')
    tecnico = models.CharField('Técnico', max_length=100, blank=True)
    fecha_ingreso = models.DateField('Fecha de ingreso', auto_now_add=True)
    fecha_inicio = models.DateField('Fecha inicio trabajo', null=True, blank=True)
    fecha_termino = models.DateField('Fecha término trabajo', null=True, blank=True)
    fecha_entrega = models.DateField('Fecha de entrega', null=True, blank=True)
    diagnostico = models.TextField('Diagnóstico / Hallazgos', blank=True)
    trabajo_realizado = models.TextField('Trabajo realizado', blank=True)
    software_instalado = models.TextField('Software instalado/desinstalado', blank=True, help_text='Listar programas instalados o removidos')
    horas_trabajadas = models.DecimalField('Horas trabajadas', max_digits=6, decimal_places=2, default=0)
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    garantia_fin = models.DateField('Garantía hasta', null=True, blank=True)
    notas_internas = models.TextField('Notas internas', blank=True)
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)

    class Meta:
        verbose_name = 'Orden de Servicio'
        verbose_name_plural = 'Órdenes de Servicio'
        ordering = ['-fecha_ingreso']

    def __str__(self):
        equipo_str = f' - {self.equipo}' if self.equipo else ''
        return f'OS #{self.id} - {self.cliente.razon_social}{equipo_str}'

    def save(self, *args, **kwargs):
        if self.estado == 'completado' and not self.garantia_fin:
            self.garantia_fin = datetime.date.today() + datetime.timedelta(days=90)
        if self.estado == 'en_curso' and not self.fecha_inicio:
            self.fecha_inicio = datetime.date.today()
        if self.estado == 'completado' and not self.fecha_termino:
            self.fecha_termino = datetime.date.today()
        super().save(*args, **kwargs)


class RepuestoUsado(models.Model):
    orden = models.ForeignKey(OrdenServicio, on_delete=models.CASCADE, related_name='repuestos', verbose_name='Orden')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, verbose_name='Producto')
    cantidad = models.IntegerField('Cantidad', default=1)
    precio_unitario = models.DecimalField('Precio unitario', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Repuesto usado'
        verbose_name_plural = 'Repuestos usados'

    def __str__(self):
        return f'{self.cantidad}x {self.producto.nombre}'


class FotoOrden(models.Model):
    orden = models.ForeignKey(OrdenServicio, on_delete=models.CASCADE, related_name='fotos', verbose_name='Orden')
    imagen = models.ImageField('Imagen', upload_to='ordenes_fotos/')
    descripcion = models.CharField('Descripción', max_length=200, blank=True)
    uploaded_at = models.DateTimeField('Subida', auto_now_add=True)

    class Meta:
        verbose_name = 'Foto'
        verbose_name_plural = 'Fotos'
