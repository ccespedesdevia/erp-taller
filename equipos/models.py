from django.db import models
from clientes.models import Cliente


class Equipo(models.Model):
    TIPO_CHOICES = [
        ('pc', 'PC'), ('notebook', 'Notebook'), ('servidor', 'Servidor'),
        ('impresora', 'Impresora'), ('red', 'Equipo de Red'),
        ('ups', 'UPS'), ('otro', 'Otro'),
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='equipos', verbose_name='Cliente')
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES)
    marca = models.CharField('Marca', max_length=100, blank=True)
    modelo = models.CharField('Modelo', max_length=100, blank=True)
    numero_serie = models.CharField('N° Serie', max_length=100, blank=True)
    numero_inventario = models.CharField('N° Inventario', max_length=100, blank=True)
    especificaciones = models.TextField('Especificaciones', blank=True, help_text='RAM, disco, CPU, SO, etc.')
    garantia_fin = models.DateField('Garantía hasta', null=True, blank=True)
    notas = models.TextField('Notas', blank=True)
    created_at = models.DateTimeField('Creado', auto_now_add=True)

    class Meta:
        verbose_name = 'Equipo'
        verbose_name_plural = 'Equipos'
        ordering = ['marca', 'modelo']

    def __str__(self):
        serie = f' [{self.numero_serie}]' if self.numero_serie else ''
        return f'{self.get_tipo_display()} {self.marca} {self.modelo}{serie}'
