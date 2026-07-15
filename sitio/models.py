from django.db import models
from django.utils.text import slugify

class ServicePage(models.Model):
    nombre = models.CharField('Nombre del servicio', max_length=200)
    slug = models.SlugField('Slug', unique=True, blank=True)
    icono = models.CharField('Ícono (Material Symbol)', max_length=50, default='settings')
    color_gradiente = models.CharField('Gradiente CSS', max_length=200, default='linear-gradient(135deg, #0066ff, #00ccff)')
    imagen = models.URLField('URL imagen', blank=True)
    descripcion_corta = models.CharField('Descripción corta', max_length=300)
    contenido = models.TextField('Contenido detallado', blank=True,
        help_text='Markdown o HTML con la descripción completa del servicio')
    beneficios = models.TextField('Beneficios', blank=True,
        help_text='Un beneficio por línea')
    meta_title = models.CharField('Meta Título', max_length=70, blank=True)
    meta_description = models.CharField('Meta Descripción', max_length=160, blank=True)
    orden = models.IntegerField('Orden', default=0)
    activo = models.BooleanField('Activo', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['orden']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

    def lista_beneficios(self):
        return [b.strip() for b in self.beneficios.split('\n') if b.strip()]

class BlogPost(models.Model):
    titulo = models.CharField('Título', max_length=200)
    slug = models.SlugField('Slug', unique=True, blank=True)
    resumen = models.TextField('Resumen', max_length=400)
    contenido = models.TextField('Contenido (HTML)')
    imagen = models.URLField('URL imagen', blank=True)
    autor = models.CharField('Autor', max_length=100, default='CACD Soluciones')
    publicado = models.BooleanField('Publicado', default=True)
    fecha_publicacion = models.DateTimeField('Fecha de publicación', auto_now_add=True)
    meta_title = models.CharField('Meta Título', max_length=70, blank=True)
    meta_description = models.CharField('Meta Descripción', max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Artículo'
        verbose_name_plural = 'Artículos'
        ordering = ['-fecha_publicacion']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        if not self.meta_title:
            self.meta_title = self.titulo[:70]
        if not self.meta_description:
            self.meta_description = self.resumen[:160]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo
