import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import Equipo
from ordenes.models import OrdenServicio


@csrf_exempt
def identificar_equipo(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST requerido'}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    hostname = (data.get('hostname') or '').strip()
    uuid_bios = (data.get('uuid_bios') or '').strip()
    mac_address = (data.get('mac_address') or '').strip()
    disco_serial = (data.get('disco_serial') or '').strip()
    motherboard_serial = (data.get('motherboard_serial') or '').strip()

    if not any([uuid_bios, mac_address, disco_serial]):
        return JsonResponse({'error': 'Se requiere uuid_bios, mac_address o disco_serial'}, status=400)

    # Buscar por huella digital
    equipo = None
    criterios = Q()
    if uuid_bios:
        criterios |= Q(uuid_bios=uuid_bios)
    if mac_address:
        criterios |= Q(mac_address=mac_address)
    if disco_serial:
        criterios |= Q(disco_serial=disco_serial)
    if motherboard_serial:
        criterios |= Q(motherboard_serial=motherboard_serial)

    equipos = Equipo.objects.filter(criterios).distinct().order_by('-created_at')

    if equipos.exists():
        equipo = equipos.first()
        created = False
    else:
        equipo = Equipo.objects.create(
            hostname=hostname,
            uuid_bios=uuid_bios,
            mac_address=mac_address,
            disco_serial=disco_serial,
            motherboard_serial=motherboard_serial,
            tipo='pc',
        )
        created = True

    # Actualizar hostname si cambió
    if hostname and hostname != equipo.hostname:
        equipo.hostname = hostname
        equipo.save(update_fields=['hostname'])

    # Buscar tickets asociados
    tickets = OrdenServicio.objects.filter(equipo=equipo).order_by('-fecha_ingreso')
    tickets_data = [
        {
            'codigo': t.codigo_seguimiento,
            'fecha': str(t.fecha_ingreso),
            'estado': t.get_estado_display(),
            'motivo': t.motivo or t.diagnostico or '',
        }
        for t in tickets
    ]

    return JsonResponse({
        'ok': True,
        'creado': created,
        'equipo_id': equipo.pk,
        'tipo': equipo.get_tipo_display(),
        'marca': equipo.marca or '',
        'modelo': equipo.modelo or '',
        'numero_serie': equipo.numero_serie or '',
        'cliente': {
            'id': equipo.cliente.pk if equipo.cliente else None,
            'razon_social': equipo.cliente.razon_social if equipo.cliente else '',
            'rut': equipo.cliente.rut if equipo.cliente else '',
        } if equipo.cliente else None,
        'tickets': tickets_data,
        'tickets_count': len(tickets_data),
    })
