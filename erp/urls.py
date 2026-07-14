import subprocess
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.http import HttpResponse
from cotizaciones.views import consultar_cotizacion

def home(request):
    return render(request, 'home.html')

def deploy(request):
    import os, sys
    out = []
    out.append("=== GIT PULL ===")
    out.append(subprocess.check_output(["git", "pull"], cwd=os.path.dirname(os.path.dirname(__file__)), stderr=subprocess.STDOUT, timeout=30).decode())
    out.append("=== MIGRATE ===")
    venv_python = os.path.join(os.path.dirname(os.path.dirname(__file__)), "venv", "bin", "python")
    out.append(subprocess.check_output([venv_python, "manage.py", "migrate"], cwd=os.path.dirname(os.path.dirname(__file__)), stderr=subprocess.STDOUT, timeout=60).decode())
    return HttpResponse("<pre>" + "\n".join(out) + "</pre>")

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls')),
    path('portal/', include('portal.urls')),
    path('api/equipos/', include('equipos.urls')),
    path('cotizaciones/<int:numero>/consultar/', consultar_cotizacion, name='cotizacion_consultar'),
    path('__deploy__/', deploy, name='deploy'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
