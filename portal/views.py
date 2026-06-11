from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from clientes.models import Cliente
from ordenes.models import OrdenServicio
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
        equipo_id = request.POST.get('equipo')
        diagnostico = request.POST.get('diagnostico', '')

        if not diagnostico.strip():
            messages.error(request, 'Describe el problema que necesitas resolver.')
            equipos = Equipo.objects.filter(cliente=cliente)
            return render(request, 'portal/orden_form.html', {'cliente': cliente, 'equipos': equipos})

        equipo = None
        if equipo_id:
            equipo = get_object_or_404(Equipo, pk=equipo_id, cliente=cliente)

        orden = OrdenServicio.objects.create(
            cliente=cliente,
            equipo=equipo,
            diagnostico=diagnostico,
            estado='pendiente',
        )
        messages.success(request, f'Ticket #{orden.id} creado correctamente.')
        return redirect('portal_orden_detail', pk=orden.pk)

    equipos = Equipo.objects.filter(cliente=cliente)
    return render(request, 'portal/orden_form.html', {'cliente': cliente, 'equipos': equipos})
