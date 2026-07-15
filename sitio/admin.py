from django.contrib import admin
from .models import ServicePage, BlogPost

@admin.register(ServicePage)
class ServicePageAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'orden', 'activo', 'slug']
    list_editable = ['orden', 'activo']
    prepopulated_fields = {'slug': ('nombre',)}
    fieldsets = [
        ('Identificación', {'fields': ['nombre', 'slug', 'orden', 'activo']}),
        ('Contenido', {'fields': ['descripcion_corta', 'contenido', 'beneficios']}),
        ('Apariencia', {'fields': ['icono', 'color_gradiente', 'imagen']}),
        ('SEO', {'fields': ['meta_title', 'meta_description']}),
    ]

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'fecha_publicacion', 'publicado', 'autor']
    list_filter = ['publicado', 'autor']
    prepopulated_fields = {'slug': ('titulo',)}
    fieldsets = [
        ('Identificación', {'fields': ['titulo', 'slug', 'publicado']}),
        ('Contenido', {'fields': ['resumen', 'contenido', 'imagen', 'autor']}),
        ('SEO', {'fields': ['meta_title', 'meta_description']}),
    ]
