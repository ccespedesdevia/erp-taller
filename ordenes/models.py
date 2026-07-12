import datetime
import os
import secrets
import string
from django.db import models
from django.conf import settings
from clientes.models import Cliente
from equipos.models import Equipo
from inventario.models import Producto


def generar_codigo():
    return 'TKT-' + ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))


class OrdenServicio(models.Model):
    codigo_seguimiento = models.CharField('Código de seguimiento', max_length=20, unique=True, blank=True, editable=False)
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
    motivo = models.TextField('Motivo del servicio', blank=True, help_text='Lo que reporta el cliente')
    contacto = models.CharField('Nombre contacto', max_length=200, blank=True)
    telefono = models.CharField('Teléfono contacto', max_length=50, blank=True)
    email_contacto = models.EmailField('Email contacto', max_length=200, blank=True)
    empresa = models.CharField('Empresa', max_length=200, blank=True)
    centro_costo = models.CharField('Centro de costo', max_length=200, blank=True)
    orden_compra_cliente = models.CharField('Orden de compra', max_length=100, blank=True, help_text='N° de OC del cliente')
    orden_compra_archivo = models.FileField('Documento OC', upload_to='ordenes_oc/', blank=True, null=True)
    oc_aprobada = models.BooleanField('OC aprobada', default=False)
    datos_identificacion = models.TextField('Datos identificación PC', blank=True, help_text='JSON con hardware, software y errores detectados por script')
    archivo_identificacion = models.FileField('Informe del cliente', upload_to='identificacion/', blank=True, null=True, help_text='.txt generado por el script que el cliente sube')
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)

    class Meta:
        verbose_name = 'Orden de Servicio'
        verbose_name_plural = 'Órdenes de Servicio'
        ordering = ['-fecha_ingreso']

    def total_neto(self):
        return sum(r.total_neto() for r in self.repuestos.all())

    def __str__(self):
        equipo_str = f' - {self.equipo}' if self.equipo else ''
        return f'OS #{self.id} - {self.cliente.razon_social}{equipo_str}'

    @property
    def informe_html(self) -> str:
        from .msinfo_parser import informe_to_html
        if not self.archivo_identificacion:
            return ''
        try:
            path = self.archivo_identificacion.path
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                return informe_to_html(content)
            try:
                content = self.archivo_identificacion.read().decode('utf-8', errors='replace')
                return informe_to_html(content)
            except Exception:
                return ''
        except Exception:
            return ''

    def save(self, *args, **kwargs):
        if not self.codigo_seguimiento:
            self.codigo_seguimiento = generar_codigo()
        if self.estado == 'completado' and not self.garantia_fin:
            self.garantia_fin = datetime.date.today() + datetime.timedelta(days=90)
        if self.estado == 'en_curso' and not self.fecha_inicio:
            self.fecha_inicio = datetime.date.today()
        if self.estado == 'completado' and not self.fecha_termino:
            self.fecha_termino = datetime.date.today()
        super().save(*args, **kwargs)


class RepuestoUsado(models.Model):
    orden = models.ForeignKey(OrdenServicio, on_delete=models.CASCADE, related_name='repuestos', verbose_name='Orden')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, verbose_name='Producto/Servicio')
    cantidad = models.IntegerField('Cantidad', default=1)
    precio_unitario = models.DecimalField('Valor unitario neto', max_digits=10, decimal_places=2, help_text='Sin IVA')

    class Meta:
        verbose_name = 'Ítem de cobro'
        verbose_name_plural = 'Detalle del cobro'

    def __str__(self):
        return f'{self.cantidad}x {self.producto.nombre}'

    def total_neto(self):
        return self.cantidad * self.precio_unitario


class FotoOrden(models.Model):
    orden = models.ForeignKey(OrdenServicio, on_delete=models.CASCADE, related_name='fotos', verbose_name='Orden')
    imagen = models.ImageField('Imagen', upload_to='ordenes_fotos/')
    descripcion = models.CharField('Descripción', max_length=200, blank=True)
    uploaded_at = models.DateTimeField('Subida', auto_now_add=True)

    class Meta:
        verbose_name = 'Foto'
        verbose_name_plural = 'Fotos'


class ComentarioTicket(models.Model):
    orden = models.ForeignKey(OrdenServicio, on_delete=models.CASCADE, related_name='comentarios', verbose_name='Orden')
    autor = models.CharField('Autor', max_length=100)
    texto = models.TextField('Mensaje')
    es_tecnico = models.BooleanField('Es del técnico', default=False)
    created_at = models.DateTimeField('Fecha', auto_now_add=True)

    class Meta:
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.autor}: {self.texto[:50]}'
