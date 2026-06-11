from django.db import models
from clientes.models import Cliente


class Equipo(models.Model):
    TIPO_CHOICES = [
        ('pc', 'PC'), ('notebook', 'Notebook'), ('servidor', 'Servidor'),
        ('impresora', 'Impresora'), ('red', 'Equipo de Red'),
        ('ups', 'UPS'), ('otro', 'Otro'),
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipos', verbose_name='Cliente')
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES)
    marca = models.CharField('Marca', max_length=100, blank=True)
    modelo = models.CharField('Modelo', max_length=100, blank=True)
    numero_serie = models.CharField('N° Serie', max_length=100, blank=True)
    numero_inventario = models.CharField('N° Inventario', max_length=100, blank=True)
    hostname = models.CharField('Nombre PC', max_length=100, blank=True, help_text='Computer name detectado por script')
    uuid_bios = models.CharField('UUID BIOS', max_length=100, blank=True, db_index=True)
    mac_address = models.CharField('Dirección MAC', max_length=20, blank=True, db_index=True)
    disco_serial = models.CharField('Serial del disco', max_length=100, blank=True)
    motherboard_serial = models.CharField('Serial motherboard', max_length=100, blank=True)
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
