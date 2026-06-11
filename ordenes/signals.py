from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import RepuestoUsado
from inventario.models import MovimientoStock


@receiver(post_save, sender=RepuestoUsado)
def descontar_stock(sender, instance, created, **kwargs):
    if created:
        instance.producto.stock_actual -= instance.cantidad
        instance.producto.save(update_fields=['stock_actual'])
        MovimientoStock.objects.create(
            producto=instance.producto,
            tipo='salida',
            cantidad=instance.cantidad,
            referencia=f'OS #{instance.orden.id}',
        )


@receiver(post_delete, sender=RepuestoUsado)
def reponer_stock(sender, instance, **kwargs):
    instance.producto.stock_actual += instance.cantidad
    instance.producto.save(update_fields=['stock_actual'])
