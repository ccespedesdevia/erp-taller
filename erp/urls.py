from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from cotizaciones.views import consultar_cotizacion

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls')),
    path('portal/', include('portal.urls')),
    path('api/equipos/', include('equipos.urls')),
    path('cotizaciones/<int:numero>/consultar/', consultar_cotizacion, name='cotizacion_consultar'),
    path('', include('sitio.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
