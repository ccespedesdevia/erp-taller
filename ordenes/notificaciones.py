import re
import logging
import urllib.request
import urllib.parse
from django.conf import settings

logger = logging.getLogger(__name__)


def formatear_telefono(numero):
    numero = re.sub(r'[^\d]', '', str(numero))
    if len(numero) == 9:  # Chile: 912345678
        numero = '569' + numero
    elif len(numero) == 11 and numero.startswith('569'):  # ya completo
        pass
    elif len(numero) == 12 and numero.startswith('+569'):
        return '+' + numero.lstrip('+')
    if not numero.startswith('+'):
        numero = '+' + numero
    return numero


def enviar_whatsapp(destinatario, mensaje):
    instance_id = getattr(settings, 'ULTRAMSG_INSTANCE_ID', None)
    token = getattr(settings, 'ULTRAMSG_TOKEN', None)
    if not instance_id or not token:
        logger.warning('UltraMSG no configurado')
        return False
    telefono = formatear_telefono(destinatario)
    data = urllib.parse.urlencode({'token': token, 'to': telefono, 'body': mensaje}).encode()
    url = f'https://api.ultramsg.com/{instance_id}/messages/chat'
    try:
        req = urllib.request.Request(url, data=data)
        resp = urllib.request.urlopen(req, timeout=10)
        result = resp.read().decode()
        logger.info(f'WhatsApp enviado a {telefono}: {result}')
        return True
    except Exception as e:
        logger.error(f'Error WhatsApp a {telefono}: {e}')
        return False


def _notificar_tecnico_whatsapp(orden, tipo, comentario=None):
    telefono = getattr(settings, 'WHATSAPP_TECNICO', None)
    if not telefono:
        return
    mensaje = (
        f'🔔 {tipo}\n'
        f'Ticket: {orden.codigo_seguimiento}\n'
        f'Cliente: {orden.cliente.razon_social}\n'
        f'Contacto: {orden.contacto or "—"} | {orden.telefono or "—"}\n'
        f'Motivo: {orden.motivo or orden.diagnostico or "—"}\n'
        f'Estado: {orden.get_estado_display()}'
    )
    if comentario:
        mensaje += f'\n\nComentario: {comentario.autor}: {comentario.texto[:200]}'
    mensaje += f'\n\nhttps://{settings.SEGUIMIENTO_URL.split("://")[-1]}/admin/ordenes/ordenservicio/{orden.pk}/change/'
    enviar_whatsapp(telefono, mensaje)


def _notificar_cliente_whatsapp(orden, tipo, mensaje_extra=''):
    if not orden.telefono:
        return
    mensaje = (
        f'🔔 {tipo}\n\n'
        f'Ticket: {orden.codigo_seguimiento}\n\n'
        f'{mensaje_extra}\n\n'
        f'Revisa: '
        f'https://{settings.SEGUIMIENTO_URL.split("://")[-1]}/portal/seguir/?codigo={orden.codigo_seguimiento}\n\n'
        f'— CACD Soluciones'
    )
    enviar_whatsapp(orden.telefono, mensaje)


def notificar_tecnico(orden, tipo, comentario=None):
    _notificar_tecnico_whatsapp(orden, tipo, comentario)


def notificar_cliente(orden, tipo, mensaje_extra=''):
    _notificar_cliente_whatsapp(orden, tipo, mensaje_extra)
