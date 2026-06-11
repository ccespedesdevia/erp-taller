import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def notificar_tecnico(orden, tipo, comentario=None):
    destinatarios = getattr(settings, 'NOTIFICACIONES_EMAIL_TECNICO', [])
    if not destinatarios:
        return
    cuerpo = (
        f'{tipo}\n\n'
        f'Ticket: {orden.codigo_seguimiento}\n'
        f'Cliente: {orden.cliente.razon_social}\n'
        f'Contacto: {orden.contacto or "—"} | {orden.telefono or "—"}\n'
        f'Email: {orden.email_contacto or "—"}\n'
        f'Motivo: {orden.motivo or orden.diagnostico or "—"}\n'
        f'Estado: {orden.get_estado_display()}\n'
    )
    if comentario:
        cuerpo += f'\nComentario: {comentario.autor}: {comentario.texto}\n'
    cuerpo += f'\nAdmin: {settings.SEGUIMIENTO_URL}/admin/ordenes/ordenservicio/{orden.pk}/change/'
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
    cuerpo = (
        f'{tipo}\n\n'
        f'Ticket: {orden.codigo_seguimiento}\n\n'
        f'{mensaje_extra}\n\n'
        f'Revisa el detalle:\n'
        f'{settings.SEGUIMIENTO_URL}/portal/seguir/?codigo={orden.codigo_seguimiento}\n\n'
        f'— CACD Soluciones'
    )
    send_mail(
        f'[{orden.codigo_seguimiento}] {tipo}',
        cuerpo,
        settings.DEFAULT_FROM_EMAIL,
        [orden.email_contacto],
        fail_silently=True,
    )
