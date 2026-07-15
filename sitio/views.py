from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from .models import ServicePage, BlogPost

META_DEFAULT = {
    'title': 'CACD Soluciones — Infraestructura, Ciberseguridad y Cloud',
    'description': 'Soluciones tecnológicas integrales en Chile. Infraestructura TI, ciberseguridad, cloud AWS y consultoría. 25 años de experiencia y 500+ proyectos exitosos.',
}

def _meta(title=None, description=None, image=None):
    return {
        'title': title or META_DEFAULT['title'],
        'description': description or META_DEFAULT['description'],
        'image': image or 'https://www.cacdsoluciones.com/og-image.jpg',
    }

def home(request):
    servicios = ServicePage.objects.filter(activo=True)
    return render(request, 'sitio/home.html', {
        'servicios': servicios,
        'meta': _meta(),
    })

def servicio_list(request):
    servicios = ServicePage.objects.filter(activo=True)
    return render(request, 'sitio/servicio_list.html', {
        'servicios': servicios,
        'meta': _meta(
            title='Servicios TI — CACD Soluciones',
            description='Ciberseguridad, Cloud AWS, Infraestructura TI, Licenciamiento, Continuidad de Negocio y Consultoría TI en Chile.'
        ),
    })

def servicio_detail(request, slug):
    servicio = get_object_or_404(ServicePage, slug=slug, activo=True)
    otros = ServicePage.objects.filter(activo=True).exclude(id=servicio.id)[:3]
    return render(request, 'sitio/servicio_detail.html', {
        'servicio': servicio,
        'otros': otros,
        'meta': _meta(
            title=servicio.meta_title or f'{servicio.nombre} — CACD Soluciones',
            description=servicio.meta_description or servicio.descripcion_corta,
        ),
    })

def blog_list(request):
    articulos = BlogPost.objects.filter(publicado=True)
    return render(request, 'sitio/blog_list.html', {
        'articulos': articulos,
        'meta': _meta(
            title='Blog — CACD Soluciones',
            description='Artículos sobre infraestructura TI, ciberseguridad, cloud computing y transformación digital para empresas en Chile.'
        ),
    })

def blog_detail(request, slug):
    articulo = get_object_or_404(BlogPost, slug=slug, publicado=True)
    return render(request, 'sitio/blog_detail.html', {
        'articulo': articulo,
        'meta': _meta(
            title=articulo.meta_title or f'{articulo.titulo} — CACD Soluciones',
            description=articulo.meta_description or articulo.resumen,
        ),
    })

def enviar_contacto(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '')
        email = request.POST.get('email', '')
        telefono = request.POST.get('telefono', '')
        mensaje = request.POST.get('mensaje', '')
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            send_mail(
                f'Nuevo contacto desde web: {nombre}',
                f'Nombre: {nombre}\nEmail: {email}\nTeléfono: {telefono}\nMensaje: {mensaje}',
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_FROM_EMAIL],
                fail_silently=True,
            )
        except Exception:
            pass
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False}, status=405)
