from django.core.mail import send_mail
from django.conf import settings


SEGUIMIENTO_URL = getattr(settings, 'SEGUIMIENTO_URL', 'http://localhost:8000')


def notificar_tecnico(orden, tipo, comentario=None):
    cuerpo = f"""🔔 {tipo}

Ticket: {orden.codigo_seguimiento}
Cliente: {orden.cliente.razon_social}
Contacto: {orden.contacto or '—'} | {orden.telefono or '—'}
Email: {orden.email_contacto or '—'}
Motivo: {orden.motivo or orden.diagnostico or '—'}
Estado: {orden.get_estado_display()}
"""
    if comentario:
        cuerpo += f"\nComentario: {comentario.autor} — {comentario.texto}\n"
    cuerpo += f"""
Ver en admin: {SEGUIMIENTO_URL}/admin/ordenes/ordenservicio/{orden.pk}/change/
"""

    destinatarios = getattr(settings, 'NOTIFICACIONES_EMAIL_TECNICO', [])
    if destinatarios:
        send_mail(
            f'[{orden.codigo_seguimiento}] {tipo}',
            cuerpo,
            settings.DEFAULT_FROM_EMAIL,
            destinatarios,
            fail_silently=True,
        )


def notificar_cliente(orden, tipo, mensaje_extra=''):
    if not orden.email_contacto:
        return
    url = f'{SEGUIMIENTO_URL}/portal/seguir/?codigo={orden.codigo_seguimiento}'
    cuerpo = f"""🔔 {tipo}

Ticket: {orden.codigo_seguimiento}

{mensaje_extra}

Revisa el detalle completo aquí:
{url}

— CACD Soluciones
"""
    send_mail(
        f'[{orden.codigo_seguimiento}] {tipo}',
        cuerpo,
        settings.DEFAULT_FROM_EMAIL,
        [orden.email_contacto],
        fail_silently=True,
    )
