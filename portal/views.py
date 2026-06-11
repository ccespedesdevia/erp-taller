import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from clientes.models import Cliente
from ordenes.models import OrdenServicio, FotoOrden
from equipos.models import Equipo


@login_required
def dashboard(request):
    try:
        cliente = request.user.cliente
    except Cliente.DoesNotExist:
        return render(request, 'portal/error.html', {'mensaje': 'Tu usuario no está vinculado a ningún cliente. Contacta al administrador.'})

    ordenes = OrdenServicio.objects.filter(cliente=cliente).order_by('-fecha_ingreso')

    context = {
        'cliente': cliente,
        'ordenes': ordenes,
        'pendientes': ordenes.filter(estado='pendiente').count(),
        'en_curso': ordenes.filter(estado='en_curso').count(),
        'completadas': ordenes.filter(estado='completado').count(),
    }
    return render(request, 'portal/dashboard.html', context)


@login_required
def orden_detail(request, pk):
    try:
        cliente = request.user.cliente
    except Cliente.DoesNotExist:
        return render(request, 'portal/error.html', {'mensaje': 'Usuario no vinculado.'})

    orden = get_object_or_404(OrdenServicio, pk=pk, cliente=cliente)
    return render(request, 'portal/orden_detail.html', {'orden': orden})


@login_required
def crear_orden(request):
    try:
        cliente = request.user.cliente
    except Cliente.DoesNotExist:
        return render(request, 'portal/error.html', {'mensaje': 'Usuario no vinculado.'})

    if request.method == 'POST':
        diagnostico = request.POST.get('diagnostico', '').strip()
        if not diagnostico:
            messages.error(request, 'Describe el problema que necesitas resolver.')
            equipos = Equipo.objects.filter(cliente=cliente)
            return render(request, 'portal/orden_form.html', {'cliente': cliente, 'equipos': equipos})

        equipo_id = request.POST.get('equipo')
        equipo = None
        if equipo_id:
            equipo = get_object_or_404(Equipo, pk=equipo_id, cliente=cliente)
        else:
            marca = request.POST.get('equipo_marca', '').strip()
            modelo = request.POST.get('equipo_modelo', '').strip()
            sistema_operativo = request.POST.get('sistema_operativo', '').strip()
            if marca or modelo:
                especs = f'SO: {sistema_operativo}' if sistema_operativo else ''
                equipo = Equipo.objects.create(
                    cliente=cliente,
                    tipo='otro',
                    marca=marca or 'Sin especificar',
                    modelo=modelo or 'Sin especificar',
                    especificaciones=especs,
                )

        nombre_contacto = request.POST.get('nombre_contacto', '').strip()
        diagnostico_completo = f'Contacto: {nombre_contacto}\n\n{diagnostico}' if nombre_contacto else diagnostico

        orden = OrdenServicio.objects.create(
            cliente=cliente,
            equipo=equipo,
            diagnostico=diagnostico_completo,
            estado='pendiente',
        )

        for f in request.FILES.getlist('fotos'):
            FotoOrden.objects.create(orden=orden, imagen=f)

        messages.success(request, f'Ticket #{orden.id} creado correctamente.')
        return redirect('portal_orden_detail', pk=orden.pk)

    equipos = Equipo.objects.filter(cliente=cliente)
    return render(request, 'portal/orden_form.html', {'cliente': cliente, 'equipos': equipos})
