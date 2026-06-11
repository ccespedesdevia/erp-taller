from django.db import models


class ActivoFijo(models.Model):
    ESTADO_CHOICES = [
        ('operativo', 'Operativo'), ('reparacion', 'En Reparación'),
        ('baja', 'Dado de Baja'),
    ]
    nombre = models.CharField('Nombre', max_length=200)
    marca = models.CharField('Marca', max_length=100, blank=True)
    modelo = models.CharField('Modelo', max_length=100, blank=True)
    numero_serie = models.CharField('N° Serie', max_length=100, blank=True)
    fecha_compra = models.DateField('Fecha de compra', null=True, blank=True)
    valor = models.DecimalField('Valor', max_digits=12, decimal_places=2, default=0)
    tecnico_asignado = models.CharField('Técnico asignado', max_length=100, blank=True)
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='operativo')
    notas = models.TextField('Notas', blank=True)
    created_at = models.DateTimeField('Creado', auto_now_add=True)

    class Meta:
        verbose_name = 'Activo Fijo'
        verbose_name_plural = 'Activos Fijos'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.get_estado_display()})'
