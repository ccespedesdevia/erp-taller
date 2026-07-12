from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from .models import Cotizacion, CotizacionConsulta


def consultar_cotizacion(request, numero):
    cotizacion = get_object_or_404(Cotizacion, numero=numero)
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        mensaje = request.POST.get('mensaje', '').strip()
        if not nombre or not mensaje:
            messages.error(request, 'Nombre y mensaje son obligatorios.')
        else:
            CotizacionConsulta.objects.create(
                cotizacion=cotizacion,
                nombre=nombre,
                email=request.POST.get('email', '').strip(),
                telefono=request.POST.get('telefono', '').strip(),
                mensaje=mensaje,
            )
            messages.success(request, 'Consulta enviada correctamente. Te contactaremos pronto.')
            return render(request, 'cotizaciones/consultar.html', {'cotizacion': cotizacion, 'enviado': True})

    return render(request, 'cotizaciones/consultar.html', {'cotizacion': cotizacion})
