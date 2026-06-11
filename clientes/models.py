from django.db import models


class Cliente(models.Model):
    razon_social = models.CharField('Razón Social', max_length=200)
    rut = models.CharField('RUT', max_length=20, unique=True)
    direccion = models.TextField('Dirección', blank=True)
    comuna = models.CharField('Comuna', max_length=100, blank=True)
    telefono = models.CharField('Teléfono', max_length=50, blank=True)
    email = models.EmailField('Email', blank=True)
    notas = models.TextField('Notas internas', blank=True)
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['razon_social']

    def __str__(self):
        return f'{self.razon_social} ({self.rut})'


class Contacto(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='contactos', verbose_name='Cliente')
    nombre = models.CharField('Nombre', max_length=200)
    cargo = models.CharField('Cargo', max_length=100, blank=True)
    telefono = models.CharField('Teléfono', max_length=50, blank=True)
    email = models.EmailField('Email', blank=True)
    es_principal = models.BooleanField('Contacto principal', default=False)

    class Meta:
        verbose_name = 'Contacto'
        verbose_name_plural = 'Contactos'

    def __str__(self):
        return f'{self.nombre} - {self.cliente.razon_social}'
