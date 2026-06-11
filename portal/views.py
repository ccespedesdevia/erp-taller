import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from clientes.models import Cliente
from ordenes.models import OrdenServicio, FotoOrden, ComentarioTicket
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
        motivo_texto = request.POST.get('diagnostico', '').strip()
        if not motivo_texto:
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

        contacto = request.POST.get('nombre_contacto', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        email = request.POST.get('email', '').strip()
        empresa = request.POST.get('empresa', '').strip()
        centro_costo = request.POST.get('centro_costo', '').strip()

        orden = OrdenServicio.objects.create(
            cliente=cliente,
            equipo=equipo,
            motivo=motivo_texto,
            contacto=contacto,
            telefono=telefono,
            email_contacto=email,
            empresa=empresa,
            centro_costo=centro_costo,
            estado='pendiente',
        )

        for f in request.FILES.getlist('fotos'):
            FotoOrden.objects.create(orden=orden, imagen=f)

        messages.success(request, f'Ticket creado correctamente.')
        return render(request, 'portal/seguir_form.html', {'codigo_creado': orden.codigo_seguimiento})

    equipos = Equipo.objects.filter(cliente=cliente)
    return render(request, 'portal/orden_form.html', {'cliente': cliente, 'equipos': equipos})


def solicitar_servicio(request):
    if request.method == 'POST':
        if request.POST.get('_url', '').strip():
            return redirect('/')

        rut = request.POST.get('rut', '').strip()
        razon_social = request.POST.get('razon_social', '').strip()
        if not rut or not razon_social:
            messages.error(request, 'RUT y Razón Social son obligatorios.')
            return render(request, 'portal/solicitar_form.html')

        cliente, _ = Cliente.objects.get_or_create(
            rut=rut,
            defaults={'razon_social': razon_social},
        )
        if cliente.razon_social != razon_social:
            cliente.razon_social = razon_social
            cliente.save()

        motivo_texto = request.POST.get('diagnostico', '').strip()
        if not motivo_texto:
            messages.error(request, 'Describe el problema.')
            return render(request, 'portal/solicitar_form.html', {'cliente': cliente})

        contacto = request.POST.get('nombre_contacto', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        email = request.POST.get('email', '').strip()
        empresa = request.POST.get('empresa', '').strip()
        centro_costo = request.POST.get('centro_costo', '').strip()

        marca = request.POST.get('equipo_marca', '').strip()
        modelo = request.POST.get('equipo_modelo', '').strip()
        sistema_operativo = request.POST.get('sistema_operativo', '').strip()
        equipo = None
        if marca or modelo:
            especs = f'SO: {sistema_operativo}' if sistema_operativo else ''
            equipo = Equipo.objects.create(
                cliente=cliente,
                tipo='otro',
                marca=marca or 'Sin especificar',
                modelo=modelo or 'Sin especificar',
                especificaciones=especs,
            )

        orden = OrdenServicio.objects.create(
            cliente=cliente,
            equipo=equipo,
            motivo=motivo_texto,
            contacto=contacto,
            telefono=telefono,
            email_contacto=email,
            empresa=empresa,
            centro_costo=centro_costo,
            estado='pendiente',
        )

        for f in request.FILES.getlist('fotos'):
            FotoOrden.objects.create(orden=orden, imagen=f)

        return render(request, 'portal/seguir_form.html', {'codigo_creado': orden.codigo_seguimiento})

    return render(request, 'portal/solicitar_form.html')


def seguir_ticket(request):
    codigo = request.GET.get('codigo', '').strip().upper()
    if codigo:
        try:
            orden = OrdenServicio.objects.get(codigo_seguimiento=codigo)
            return render(request, 'portal/seguir_resultado.html', {'orden': orden})
        except OrdenServicio.DoesNotExist:
            return render(request, 'portal/seguir_form.html', {'error': f'No se encontró ningún ticket con el código {codigo}.'})
    return render(request, 'portal/seguir_form.html')


def subir_oc(request, pk):
    orden = get_object_or_404(OrdenServicio, pk=pk)
    if orden.estado not in ('pendiente', 'en_curso'):
        messages.error(request, 'No puedes modificar la OC en este estado.')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    if request.method == 'POST':
        oc_numero = request.POST.get('orden_compra_cliente', '').strip()
        oc_archivo = request.FILES.get('orden_compra_archivo')
        if oc_numero:
            orden.orden_compra_cliente = oc_numero
        if oc_archivo:
            orden.orden_compra_archivo = oc_archivo
        if oc_numero or oc_archivo:
            orden.oc_aprobada = False
            orden.save()
            messages.success(request, 'Orden de compra registrada.')
        else:
            messages.error(request, 'Ingresa al menos el número de OC.')

    return redirect(request.META.get('HTTP_REFERER', '/'))


def subir_identificacion(request, pk):
    orden = get_object_or_404(OrdenServicio, pk=pk)
    if request.method == 'POST' and request.FILES.get('archivo_identificacion'):
        orden.archivo_identificacion = request.FILES['archivo_identificacion']
        orden.save(update_fields=['archivo_identificacion'])
        messages.success(request, 'Informe subido correctamente.')
    return redirect(request.META.get('HTTP_REFERER', '/'))


def ticket_pdf(request, pk):
    orden = get_object_or_404(OrdenServicio, pk=pk)
    return render(request, 'portal/ticket_pdf.html', {'orden': orden})


def comentar_ticket(request, pk):
    texto = request.POST.get('texto', '').strip()
    if not texto:
        messages.error(request, 'Escribe un mensaje.')
    else:
        orden = get_object_or_404(OrdenServicio, pk=pk)
        autor = 'Anónimo'
        es_tecnico = False
        if request.user.is_authenticated:
            try:
                cliente = request.user.cliente
                autor = cliente.razon_social[:100]
            except Cliente.DoesNotExist:
                autor = request.user.get_full_name() or request.user.username
                es_tecnico = True
        else:
            autor_nombre = request.POST.get('autor', '').strip()
            if autor_nombre:
                autor = autor_nombre
        ComentarioTicket.objects.create(orden=orden, autor=autor, texto=texto, es_tecnico=es_tecnico)
        messages.success(request, 'Comentario agregado.')
    referer = request.META.get('HTTP_REFERER', '/')
    return redirect(referer)



