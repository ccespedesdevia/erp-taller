from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import OrdenServicio, ComentarioTicket
from .notificaciones import notificar_tecnico, notificar_cliente


@receiver(post_save, sender=OrdenServicio)
def orden_modificada(sender, instance, created, **kwargs):
    if created:
        notificar_tecnico(instance, 'Nuevo ticket creado')
        notificar_cliente(instance, 'Ticket creado',
                          'Tu solicitud de servicio fue recibida. Pronto te contactaremos.')
    else:
        notificar_tecnico(instance, 'Ticket actualizado')
        notificar_cliente(instance, 'Ticket actualizado',
                          'Tu ticket fue actualizado por el técnico. Ingresa para ver los cambios.')


@receiver(post_save, sender=ComentarioTicket)
def comentario_creado(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.es_tecnico:
        notificar_cliente(instance.orden, 'Nueva respuesta del técnico',
                          f'{instance.autor} respondió: {instance.texto}')
    else:
        notificar_tecnico(instance.orden, 'Nuevo comentario del cliente', comentario=instance)
